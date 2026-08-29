"""
Embedding provider interface.

Two implementations:
- LocalEmbedder  : sentence-transformers (default, no API key needed)
- OpenAIEmbedder : OpenAI / any OpenAI-compatible embeddings endpoint

Select via EMBEDDING_PROVIDER env var ("local" | "openai").
"""
from abc import ABC, abstractmethod

import numpy as np

from app.core.config import settings


class BaseEmbedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Return float32 array of shape (len(texts), dim)."""

    @abstractmethod
    def embed_one(self, text: str) -> np.ndarray:
        """Return float32 array of shape (dim,)."""


class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False).astype("float32")

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self):
        import openai
        self._client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        self._model = settings.OPENAI_EMBEDDING_MODEL

    def embed(self, texts: list[str]) -> np.ndarray:
        response = self._client.embeddings.create(input=texts, model=self._model)
        vectors = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        return np.array(vectors, dtype="float32")

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]


def get_embedder() -> BaseEmbedder:
    if settings.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbedder()
    return LocalEmbedder()


# Module-level singleton — loaded once on first import
_embedder: BaseEmbedder | None = None


def embedder() -> BaseEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder
