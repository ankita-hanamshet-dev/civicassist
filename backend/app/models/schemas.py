from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    conversation_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    category: Optional[str]
    subcategory: Optional[str]
    language: str
    sources: List[str]
    chunks_used: int
    session_id: Optional[str]


class IngestResponse(BaseModel):
    status: str
    pdf_documents: int
    web_pages: int
    total_chunks_embedded: int
    index_path: str


class StatsResponse(BaseModel):
    collection_name: str
    total_chunks: int
    status: str
