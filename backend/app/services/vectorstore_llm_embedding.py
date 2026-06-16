"""
Embedding adapter using the generic LLM embedding endpoint.
This is used by the vectorstore to generate embeddings via an external LLM API.
"""
from typing import List

from app.services.llm import create_embedding


def embed_text(text: str, model_name: str) -> List[float]:
    return create_embedding(text=text, model=model_name)
