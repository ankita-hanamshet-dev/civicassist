from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from app.models.schemas import IngestResponse, StatsResponse
from app.services.ingestion import ingest_pdfs
from app.services.scraper import scrape_gub_uy
from app.services.indexer import build_index
from app.services.vectorstore import embed_all_documents, get_collection_stats

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(background_tasks: BackgroundTasks):
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
async def reindex():
    """Rebuild INDEX.md and re-embed from existing Markdown files."""
    try:
        index_path = build_index()
        chunks = embed_all_documents()
        return {"status": "success", "index_path": index_path, "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def stats():
    try:
        s = get_collection_stats()
        return StatsResponse(
            collection_name=s["collection"],
            total_chunks=s["total_chunks"],
            status="ok",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
