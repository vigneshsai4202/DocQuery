"""
Centralized application configuration.

All settings are read from environment variables (optionally loaded from a
.env file in local development). See `.env.example` for the full list of
variables and their meaning.
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App metadata ---
    APP_NAME: str = "DocuQuery"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # --- Database (Neon Postgres) ---
    # Example: postgresql+psycopg2://user:password@ep-xxx.neon.tech/dbname?sslmode=require
    DATABASE_URL: str

    # --- JWT auth ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- File upload ---
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_UPLOAD_EXTENSIONS: str = ".pdf"
    UPLOAD_DIR: str = str(BASE_DIR / "storage" / "uploads")

    # --- Chunking strategy ---
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 50

    # --- Embeddings provider ---
    # "local" uses sentence-transformers, "openai" uses OpenAI's embeddings API.
    EMBEDDING_PROVIDER: Literal["local", "openai"] = "local"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 384  # all-MiniLM-L6-v2 output dimension

    # --- Vector store (FAISS) ---
    VECTOR_STORE_DIR: str = str(BASE_DIR / "storage" / "vector_store")
    TOP_K_RESULTS: int = 5

    # --- LLM provider ---
    # "ollama": local Ollama server (free, no API key)
    # "openai": any OpenAI-compatible chat completions API (OpenAI, Azure OpenAI, etc.)
    # "huggingface": Hugging Face Inference API
    LLM_PROVIDER: Literal["ollama", "openai", "huggingface"] = "ollama"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_MODEL: str = "meta-llama/Llama-3.2-3B-Instruct"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_upload_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",") if ext.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
