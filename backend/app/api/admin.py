from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from pathlib import Path
from loguru import logger
import yaml

from app.core.config import get_settings
import app.core.config as _config_module
from app.models.schemas import AdminLoginRequest, ConfigResponse, IngestResponse, LLMConfigUpdate, PathsConfigUpdate, StatsResponse
from app.services.ingestion import ingest_pdfs
from app.services.scraper import scrape_gub_uy
from app.services.indexer import build_index
from app.services.vectorstore import embed_all_documents, get_collection_stats

security = HTTPBasic()
router = APIRouter(prefix="/admin", tags=["admin"])


def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    settings = get_settings()
    is_valid_username = secrets.compare_digest(credentials.username, settings.admin.username)
    is_valid_password = secrets.compare_digest(credentials.password, settings.admin.password)
    if not (is_valid_username and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.post("/auth")
async def auth(request: AdminLoginRequest):
    settings = get_settings()
    if not (
        secrets.compare_digest(request.username, settings.admin.username)
        and secrets.compare_digest(request.password, settings.admin.password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )
    return {"status": "ok", "message": "Authenticated"}


@router.post("/ingest", response_model=IngestResponse)
async def ingest(background_tasks: BackgroundTasks, _admin: str = Depends(get_current_admin)):
    """
    Trigger full ingestion pipeline:
    1. Ingest PDFs → Markdown
    2. Scrape gub.uy → Markdown
    3. Build INDEX.md
    4. Embed all into ChromaDB
    """
    try:
        logger.info("Starting PDF ingestion…")
        pdf_meta = ingest_pdfs()

        logger.info("Starting web scraping…")
        web_meta = scrape_gub_uy()

        all_meta = pdf_meta + web_meta

        logger.info("Building index…")
        index_path = build_index(extra_metadata=all_meta)

        logger.info("Embedding documents…")
        chunks = embed_all_documents()

        return IngestResponse(
            status="success",
            pdf_documents=len(pdf_meta),
            web_pages=len(web_meta),
            total_chunks_embedded=chunks,
            index_path=index_path,
        )
    except Exception as e:
        logger.exception(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex(_admin: str = Depends(get_current_admin)):
    """Rebuild INDEX.md and re-embed from existing Markdown files."""
    try:
        index_path = build_index()
        chunks = embed_all_documents()
        return {"status": "success", "index_path": index_path, "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def stats(_admin: str = Depends(get_current_admin)):
    try:
        s = get_collection_stats()
        return StatsResponse(
            collection_name=s["collection"],
            total_chunks=s["total_chunks"],
            status="ok",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _settings_to_response(s) -> ConfigResponse:
    return ConfigResponse(
        llm={
            "api_endpoint": s.llm.api_endpoint,
            "model_name": s.llm.model_name,
            "temperature": s.llm.temperature,
            "max_tokens": s.llm.max_tokens,
            "chat_endpoint": s.llm.chat_endpoint,
            "embedding_endpoint": s.llm.embedding_endpoint,
        },
        paths={
            "raw_pdfs": s.paths.raw_pdfs,
            "markdown_output": s.paths.markdown_output,
            "vectorstore": s.paths.vectorstore,
            "index_file": s.paths.index_file,
        },
    )


@router.get("/config", response_model=ConfigResponse)
async def config(_admin: str = Depends(get_current_admin)):
    return _settings_to_response(get_settings())


@router.put("/config/llm")
async def update_llm_config(body: LLMConfigUpdate, _admin: str = Depends(get_current_admin)):
    """Persist LLM settings back to config.yaml and reload the singleton."""
    path = _find_config_yaml()

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    llm_section = raw.setdefault("llm", {})
    update_data = body.model_dump(exclude_none=True)
    llm_section.update(update_data)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    _config_module._settings = None
    return _settings_to_response(get_settings())


def _find_config_yaml() -> Path:
    import os
    path = Path(os.getenv("CONFIG_PATH", "./config/config.yaml"))
    if not path.exists():
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / "config" / "config.yaml"
    if not path.exists():
        raise HTTPException(status_code=500, detail="config.yaml not found")
    return path


@router.put("/config/paths")
async def update_paths_config(body: PathsConfigUpdate, _admin: str = Depends(get_current_admin)):
    """Persist paths settings back to config.yaml and reload the singleton."""
    path = _find_config_yaml()

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    paths_section = raw.setdefault("paths", {})
    paths_section.update(body.model_dump(exclude_none=True))

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    _config_module._settings = None
    return _settings_to_response(get_settings())
