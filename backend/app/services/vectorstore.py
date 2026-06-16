"""
Vector Store Service (ChromaDB)
Embeds all Markdown files and provides semantic retrieval.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import chromadb
from chromadb.utils import embedding_functions
from loguru import logger

from app.core.config import get_settings

_client: Optional[chromadb.PersistentClient] = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(
            path=str(Path(settings.chromadb.persist_directory))
        )
    return _client


def _get_collection():
    global _collection
    if _collection is None:
        settings = get_settings()
        client = _get_client()
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=settings.chromadb.embedding_model
            )
        _collection = client.get_or_create_collection(
            name=settings.chromadb.collection_name,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def _strip_frontmatter(content: str) -> Tuple[Dict, str]:
    """Return (frontmatter_dict, body_text)."""
    import yaml
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(content[3:end]) or {}
                body = content[end + 3:].strip()
                return fm, body
            except Exception:
                pass
    return {}, content


def embed_all_documents() -> int:
    """Embed (or re-embed) all Markdown files into ChromaDB. Returns doc count."""
    settings = get_settings()
    md_dir = Path(settings.paths.markdown_output)
    collection = _get_collection()

    md_files = [f for f in md_dir.glob("*.md") if f.name != "INDEX.md"]
    logger.info(f"Embedding {len(md_files)} Markdown files into ChromaDB…")

    total_chunks = 0
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        fm, body = _strip_frontmatter(content)

        chunks = _chunk_text(body)
        ids = [f"{md_file.stem}__chunk{i}" for i in range(len(chunks))]
        metas = [
            {
                "filename": md_file.name,
                "title": fm.get("title", md_file.stem),
                "category": fm.get("category", "unknown"),
                "subcategory": fm.get("subcategory", ""),
                "source": fm.get("source", ""),
            }
            for _ in chunks
        ]

        # Upsert to avoid duplicates on re-index
        collection.upsert(ids=ids, documents=chunks, metadatas=metas)
        total_chunks += len(chunks)
        logger.debug(f"  {md_file.name}: {len(chunks)} chunk(s)")

    logger.success(f"Embedded {total_chunks} chunks from {len(md_files)} files.")
    return total_chunks


def retrieve(
    query: str,
    category_filter: Optional[str] = None,
    subcategory_filter: Optional[str] = None,
    n_results: int = 8,
) -> List[Dict]:
    """
    Semantic search over the vector store.
    Optionally filter by category and/or subcategory.
    Returns list of dicts with keys: text, metadata, distance.
    """
    collection = _get_collection()
    where: Optional[Dict] = None

    if category_filter and subcategory_filter:
        where = {
            "$and": [
                {"category": {"$eq": category_filter}},
                {"subcategory": {"$eq": subcategory_filter}},
            ]
        }
    elif category_filter:
        where = {"category": {"$eq": category_filter}}
    elif subcategory_filter:
        where = {"subcategory": {"$eq": subcategory_filter}}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []

    output = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        output.append({"text": doc, "metadata": meta, "distance": dist})

    return output


def get_collection_stats() -> Dict:
    col = _get_collection()
    count = col.count()
    return {"collection": col.name, "total_chunks": count}
