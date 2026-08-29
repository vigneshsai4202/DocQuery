"""
Tests for the embedding + vector store pipeline.
The sentence-transformers model is mocked so tests run without GPU/download.
"""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch


def _fake_embedder(dim: int = 384):
    emb = MagicMock()
    emb.embed.side_effect = lambda texts: np.random.rand(len(texts), dim).astype("float32")
    emb.embed_one.side_effect = lambda text: np.random.rand(dim).astype("float32")
    return emb


def test_vector_store_add_and_search(tmp_path):
    from app.services.vector_store import VectorStore
    import app.services.vector_store as vs_module

    # Point store at a temp dir
    original_index = vs_module._INDEX_PATH
    original_meta = vs_module._META_PATH
    vs_module._INDEX_PATH = tmp_path / "index.faiss"
    vs_module._META_PATH = tmp_path / "meta.json"

    try:
        store = VectorStore()
        vectors = np.random.rand(3, 384).astype("float32")
        chunk_ids = ["chunk-1", "chunk-2", "chunk-3"]
        faiss_ids = store.add(vectors, chunk_ids, "doc-1")
        assert len(faiss_ids) == 3

        query = np.random.rand(384).astype("float32")
        results = store.search(query, top_k=2)
        assert len(results) == 2
        assert all(isinstance(r[0], str) for r in results)
        assert all(isinstance(r[1], float) for r in results)
    finally:
        vs_module._INDEX_PATH = original_index
        vs_module._META_PATH = original_meta


def test_vector_store_delete_by_document(tmp_path):
    from app.services.vector_store import VectorStore
    import app.services.vector_store as vs_module

    vs_module._INDEX_PATH = tmp_path / "index.faiss"
    vs_module._META_PATH = tmp_path / "meta.json"

    try:
        store = VectorStore()
        v1 = np.random.rand(3, 384).astype("float32")
        v2 = np.random.rand(2, 384).astype("float32")
        store.add(v1, ["c1", "c2", "c3"], "doc-A")
        store.add(v2, ["c4", "c5"], "doc-B")
        assert store.total() == 5

        store.delete_by_document("doc-A")
        assert store.total() == 2
    finally:
        vs_module._INDEX_PATH = tmp_path / "index.faiss"
        vs_module._META_PATH = tmp_path / "meta.json"


def test_retrieve_chunks_empty_store(auth_client, db):
    """retrieve_chunks returns [] when the vector store is empty."""
    client, _ = auth_client
    with patch("app.services.rag.vector_store") as mock_vs:
        mock_vs.return_value.search.return_value = []
        with patch("app.services.rag.embedder") as mock_emb:
            mock_emb.return_value.embed_one.return_value = np.zeros(384, dtype="float32")
            from app.services.rag import retrieve_chunks
            results = retrieve_chunks("test query", 5, db)
    assert results == []
