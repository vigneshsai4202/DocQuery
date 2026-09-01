"""
pgvector-backed vector store.
Replaces FAISS — vectors are stored directly in the chunks.embedding column.
No local files, survives redeploys, scoped per user via document ownership.
"""
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.orm import Chunk, Document


def add_embeddings(db: Session, chunk_ids: list[str], vectors: list[list[float]]) -> None:
    """Write embedding vectors into existing Chunk rows."""
    for chunk_id, vec in zip(chunk_ids, vectors):
        db.query(Chunk).filter(Chunk.id == chunk_id).update({"embedding": vec})
    db.commit()


def search(
    db: Session,
    query_vector: list[float],
    top_k: int,
    document_ids: list[str] | None = None,
) -> list[tuple[str, float]]:
    """
    Return [(chunk_id, l2_distance), ...] ordered by ascending distance.
    Optionally filter to specific document_ids.
    """
    from pgvector.sqlalchemy import Vector
    import sqlalchemy as sa

    q = db.query(Chunk).filter(Chunk.embedding.isnot(None))
    if document_ids:
        q = q.filter(Chunk.document_id.in_(document_ids))

    # Use a labelled distance column so we can read it back without a second SQL call
    distance_col = Chunk.embedding.l2_distance(query_vector).label("distance")
    rows = (
        db.query(Chunk, distance_col)
        .filter(Chunk.embedding.isnot(None))
        .order_by(distance_col)
        .limit(top_k)
        .all()
    )
    if document_ids:
        rows = [
            (c, d) for c, d in rows if c.document_id in document_ids
        ]
    return [(c.id, float(d)) for c, d in rows]


def delete_by_document(db: Session, document_id: str) -> None:
    """Null out embeddings for a document (chunks are deleted via CASCADE anyway)."""
    db.query(Chunk).filter(Chunk.document_id == document_id).update({"embedding": None})
    db.commit()
