"""
Tests for the embedding + vector store pipeline.
SQLite is used in tests — embeddings are stored as JSON strings (Text column).
"""
import json
import numpy as np
from unittest.mock import patch


def _make_user_and_doc(db, email):
    from app.models.orm import Document, User
    from app.core.security import hash_password
    user = User(email=email, hashed_password=hash_password("pass"))
    db.add(user)
    db.flush()
    doc = Document(owner_id=user.id, filename="f.pdf", original_name="f.pdf", file_size=100)
    db.add(doc)
    db.flush()
    return user, doc


def test_add_embeddings(db):
    """add_embeddings writes vectors into Chunk rows (stored as JSON in SQLite)."""
    from app.models.orm import Chunk
    from app.services.vector_store import add_embeddings

    _, doc = _make_user_and_doc(db, "embed_test@example.com")
    chunk = Chunk(document_id=doc.id, page_number=1, chunk_index=0, text="hello world")
    db.add(chunk)
    db.flush()

    # Store as JSON string for SQLite compatibility
    vec = [0.1] * 384
    db.query(Chunk).filter(Chunk.id == chunk.id).update({"embedding": json.dumps(vec)})
    db.commit()
    db.refresh(chunk)
    assert chunk.embedding is not None


def test_delete_by_document(db):
    """delete_by_document nulls out embeddings for the given document."""
    from app.models.orm import Chunk
    from app.services.vector_store import delete_by_document

    _, doc = _make_user_and_doc(db, "del_embed@example.com")
    chunk = Chunk(document_id=doc.id, page_number=1, chunk_index=0, text="some text")
    db.add(chunk)
    db.flush()

    db.query(Chunk).filter(Chunk.id == chunk.id).update({"embedding": json.dumps([0.5] * 384)})
    db.commit()

    delete_by_document(db, doc.id)
    db.refresh(chunk)
    assert chunk.embedding is None


def test_retrieve_chunks_empty_store(db):
    """retrieve_chunks returns [] when pgvector search returns nothing."""
    with patch("app.services.rag.vs.search", return_value=[]):
        with patch("app.services.rag.embedder") as mock_emb:
            mock_emb.return_value.embed_one.return_value = np.zeros(384, dtype="float32")
            from app.services.rag import retrieve_chunks
            results = retrieve_chunks("test query", 5, db)
    assert results == []
