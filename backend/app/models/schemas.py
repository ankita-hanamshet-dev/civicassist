from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    conversation_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None
    language: Optional[str] = None  # "es" or "en"; overrides auto-detection


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


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class LLMConfigResponse(BaseModel):
    api_endpoint: str
    model_name: str
    temperature: float
    max_tokens: int
    chat_endpoint: str
    embedding_endpoint: str


class PathsConfigResponse(BaseModel):
    raw_pdfs: str
    markdown_output: str
    vectorstore: str
    index_file: str


class LLMConfigUpdate(BaseModel):
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    chat_endpoint: Optional[str] = None
    embedding_endpoint: Optional[str] = None


class PathsConfigUpdate(BaseModel):
    raw_pdfs: Optional[str] = None
    markdown_output: Optional[str] = None
    vectorstore: Optional[str] = None
    index_file: Optional[str] = None


class ConfigResponse(BaseModel):
    llm: LLMConfigResponse
    paths: Optional[PathsConfigResponse] = None


class StatsResponse(BaseModel):
    collection_name: str
    total_chunks: int
    status: str
