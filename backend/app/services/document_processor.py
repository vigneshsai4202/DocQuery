"""
Document ingestion pipeline.

Steps:
  1. Extract text per page from the PDF (pypdf).
  2. Chunk the text (sliding window, token-approximate).
  3. Embed all chunks (sentence-transformers or OpenAI).
  4. Write Chunk rows + embeddings to Postgres (pgvector).
  5. Update Document status.
"""
from sqlalchemy.orm import Session

from app.models.orm import Chunk, Document
from app.services.chunking import chunk_pages
from app.services.embeddings import embedder
from app.services.vector_store import add_embeddings


def extract_pages(file_path: str) -> dict[int, str]:
    """Return {page_number (1-based): text} for every page in the PDF."""
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    pages: dict[int, str] = {}
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages[i] = text
    return pages


def ingest_document(document_id: str, file_path: str, db: Session) -> None:
    """Run the full ingestion pipeline for a document. Updates DB in-place."""
    doc: Document | None = db.get(Document, document_id)
    if doc is None:
        raise ValueError(f"Document {document_id} not found")

    doc.status = "processing"
    db.commit()

    try:
        pages = extract_pages(file_path)
        doc.page_count = len(pages)

        chunks = chunk_pages(pages)
        if not chunks:
            doc.status = "error"
            doc.error_message = "No extractable text found in PDF."
            db.commit()
            return

        # Persist Chunk rows
        chunk_objs = []
        for c in chunks:
            obj = Chunk(
                document_id=document_id,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                text=c.text,
            )
            db.add(obj)
            chunk_objs.append(obj)
        db.flush()  # get IDs without committing

        # Embed and store in pgvector
        texts = [c.text for c in chunks]
        vectors = embedder().embed(texts)
        chunk_ids = [obj.id for obj in chunk_objs]
        add_embeddings(db, chunk_ids, vectors.tolist())

        doc.status = "ready"
        db.commit()

    except Exception as exc:
        db.rollback()
        doc = db.get(Document, document_id)
        if doc:
            doc.status = "error"
            doc.error_message = str(exc)
            db.commit()
        raise
