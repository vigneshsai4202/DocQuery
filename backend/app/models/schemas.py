from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "secret123"}}}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "secret123"}}}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: str
    filename: str
    original_name: str
    file_size: int
    page_count: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Chunks / Search ───────────────────────────────────────────────────────────

class ChunkOut(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    chunk_index: int
    text: str
    score: float


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)

    model_config = {"json_schema_extra": {"example": {"query": "What is the main topic?", "top_k": 5}}}


class SearchResponse(BaseModel):
    results: list[ChunkOut]


# ── RAG / Query ───────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What are the key findings?",
                "conversation_id": None,
                "top_k": 5,
            }
        }
    }


class QueryResponse(BaseModel):
    answer: str
    sources: list[ChunkOut]
    conversation_id: str
    message_id: str


# ── Conversations ─────────────────────────────────────────────────────────────

class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: list[dict[str, Any]] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    messages: list[MessageOut]

    model_config = {"from_attributes": True}
