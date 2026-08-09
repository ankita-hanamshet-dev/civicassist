"""
Core configuration loader — reads config.yaml + .env overrides.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel
from loguru import logger

load_dotenv()


class APIConfig(BaseModel):
    base_url: str = "http://localhost:8000"
    prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000"]


class LLMConfig(BaseModel):
    api_endpoint: str = "https://api.anthropic.com"
    api_key: str = ""
    model_name: str = "claude-sonnet-4-5"
    temperature: float = 0.2
    max_tokens: int = 2048
    chat_endpoint: str = "/v1/chat/completions"
    embedding_endpoint: str = "/v1/embeddings"


class PathsConfig(BaseModel):
    raw_pdfs: str = "./data/raw_pdfs"
    markdown_output: str = "./data/markdown"
    vectorstore: str = "./data/vectorstore"
    index_file: str = "./data/markdown/INDEX.md"


class ChromaConfig(BaseModel):
    collection_name: str = "uruguay_law"
    persist_directory: str = "./data/vectorstore"
    embedding_model: str = "all-MiniLM-L6-v2"


class ScrapingConfig(BaseModel):
    base_urls: List[str] = ["https://www.gub.uy/tramites/"]
    target_keywords: List[str] = []
    delay_seconds: float = 1.5
    timeout_seconds: int = 30


class AppConfig(BaseModel):
    name: str = "CivicAssist"
    version: str = "1.0.0"
    debug: bool = False


class AdminConfig(BaseModel):
    username: str = "admin"
    password: str = "admin"


class Settings(BaseModel):
    app: AppConfig = AppConfig()
    api: APIConfig = APIConfig()
    llm: LLMConfig = LLMConfig()
    admin: AdminConfig = AdminConfig()
    paths: PathsConfig = PathsConfig()
    chromadb: ChromaConfig = ChromaConfig()
    scraping: ScrapingConfig = ScrapingConfig()
    categories: Dict[str, Any] = {}


def _resolve_env_vars(value: Any) -> Any:
    """Recursively resolve ${ENV_VAR} placeholders."""
    if isinstance(value, str):
        if value.startswith("${") and value.endswith("}"):
            env_name = value[2:-1]
            return os.getenv(env_name, "")
        return value
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(i) for i in value]
    return value


def _find_config_path(config_path: Path) -> Path:
    if config_path.exists():
        return config_path

    # If running inside backend/, look for repo-root config/config.yaml
    repo_root = Path(__file__).resolve().parents[3]
    repo_candidate = repo_root / "config" / "config.yaml"
    if repo_candidate.exists():
        return repo_candidate

    # Search upward from current working directory for config/config.yaml
    for parent in Path.cwd().resolve().parents:
        candidate = parent / "config" / "config.yaml"
        if candidate.exists():
            return candidate

    return config_path


def _resolve_path_values(raw: Dict, base_dir: Path) -> Dict:
    if not isinstance(raw, dict):
        return raw

    paths = raw.get("paths")
    if isinstance(paths, dict):
        for key, value in paths.items():
            if isinstance(value, str):
                p = Path(value)
                if not p.is_absolute():
                    raw["paths"][key] = str((base_dir / p).resolve())

    chromadb = raw.get("chromadb")
    if isinstance(chromadb, dict):
        persist_dir = chromadb.get("persist_directory")
        if isinstance(persist_dir, str):
            p = Path(persist_dir)
            if not p.is_absolute():
                raw["chromadb"]["persist_directory"] = str((base_dir / p).resolve())

    return raw


def load_settings(config_path: Optional[str] = None) -> Settings:
    config_path = config_path or os.getenv("CONFIG_PATH", "./config/config.yaml")
    path = _find_config_path(Path(config_path))

    if not path.exists():
        logger.warning(f"Config file not found at {path}; using defaults.")
        raw: Dict = {}
    else:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    raw = _resolve_env_vars(raw)
    repo_root = path.parent.parent
    raw = _resolve_path_values(raw, repo_root)

    # Support legacy anthropic config block by mapping it into llm.
    if "anthropic" in raw and "llm" not in raw and isinstance(raw["anthropic"], dict):
        raw["llm"] = {
            "api_endpoint": raw["anthropic"].get("api_endpoint", "https://api.anthropic.com"),
            "api_key": raw["anthropic"].get("api_key", ""),
            "model_name": raw["anthropic"].get("model", "claude-sonnet-4-5"),
            "max_tokens": raw["anthropic"].get("max_tokens", 2048),
            "temperature": raw["anthropic"].get("temperature", 0.2),
            "chat_endpoint": raw["anthropic"].get("chat_endpoint", "/v1/chat/completions"),
            "embedding_endpoint": raw["anthropic"].get("embedding_endpoint", "/v1/embeddings"),
        }

    if path.exists():
        logger.info(f"Loaded configuration from {path}")
    logger.info("Resolved paths:")
    if isinstance(raw.get("paths"), dict):
        for key, value in raw["paths"].items():
            logger.info(f"  paths.{key} = {value}")
    if isinstance(raw.get("chromadb"), dict) and raw["chromadb"].get("persist_directory"):
        logger.info(f"  chromadb.persist_directory = {raw['chromadb']['persist_directory']}")

    # Override LLM configuration values from environment variables if present.
    api_key_env = os.getenv("LLM_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
    if api_key_env:
        if "llm" in raw:
            raw["llm"]["api_key"] = api_key_env
        else:
            raw.setdefault("llm", {})["api_key"] = api_key_env

    for env_name, raw_key in [
        ("LLM_API_ENDPOINT", "api_endpoint"),
        ("LLM_CHAT_ENDPOINT", "chat_endpoint"),
        ("LLM_EMBEDDING_ENDPOINT", "embedding_endpoint"),
        ("LLM_MODEL_NAME", "model_name"),
    ]:
        env_value = os.getenv(env_name, "")
        if env_value:
            raw.setdefault("llm", {})[raw_key] = env_value

    admin_username = os.getenv("ADMIN_USERNAME", "")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if admin_username:
        raw.setdefault("admin", {})["username"] = admin_username
    if admin_password:
        raw.setdefault("admin", {})["password"] = admin_password

    return Settings(**raw)


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings
