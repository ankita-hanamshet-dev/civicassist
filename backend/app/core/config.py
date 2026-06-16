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


class AnthropicConfig(BaseModel):
    api_key: str = ""
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 2048
    temperature: float = 0.2


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
    base_url: str = "https://www.gub.uy/tramites/"
    target_keywords: List[str] = []
    delay_seconds: float = 1.5
    timeout_seconds: int = 30


class AppConfig(BaseModel):
    name: str = "CivicAssist"
    version: str = "1.0.0"
    debug: bool = False


class Settings(BaseModel):
    app: AppConfig = AppConfig()
    api: APIConfig = APIConfig()
    anthropic: AnthropicConfig = AnthropicConfig()
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

    if path.exists():
        logger.info(f"Loaded configuration from {path}")
    logger.info("Resolved paths:")
    if isinstance(raw.get("paths"), dict):
        for key, value in raw["paths"].items():
            logger.info(f"  paths.{key} = {value}")
    if isinstance(raw.get("chromadb"), dict) and raw["chromadb"].get("persist_directory"):
        logger.info(f"  chromadb.persist_directory = {raw['chromadb']['persist_directory']}")

    # Override API key from env if present
    api_key_env = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key_env and "anthropic" in raw:
        raw["anthropic"]["api_key"] = api_key_env
    elif api_key_env:
        raw.setdefault("anthropic", {})["api_key"] = api_key_env

    return Settings(**raw)


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings
