import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user_id
from app.db.base import get_db
from app.models.orm import Document
from app.models.schemas import DocumentOut
from app.services import vector_store as vs

router = APIRouter(prefix="/documents", tags=["documents"])

_UPLOAD_DIR = Path(settings.UPLOAD_DIR)
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _run_ingestion(document_id: str, file_path: str) -> None:
    """Background task: runs ingestion with its own DB session."""
    from app.db.base import SessionLocal
    from app.services.document_processor import ingest_document
    db = SessionLocal()
    try:
        ingest_document(document_id, file_path, db)
    except Exception:
        pass  # errors are written to document.error_message inside ingest_document
    finally:
        db.close()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upload a PDF. Ingestion (chunking + embedding) runs in the background."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_upload_extensions_list:
        raise HTTPException(
            status_code=400,
            detail=f"Only {settings.ALLOWED_UPLOAD_EXTENSIONS} files are accepted",
        )

    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
        )

    doc_id = str(uuid.uuid4())
    stored_name = f"{doc_id}{ext}"
    file_path = _UPLOAD_DIR / stored_name
    file_path.write_bytes(content)

    doc = Document(
        id=doc_id,
        owner_id=user_id,
        filename=stored_name,
        original_name=file.filename or stored_name,
        file_size=len(content),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(_run_ingestion, doc_id, str(file_path))
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List all documents for the current user, newest first."""
    return (
        db.query(Document)
        .filter(Document.owner_id == user_id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a single document by ID."""
    doc = db.get(Document, document_id)
    if not doc or doc.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a document, its vectors, and its stored file."""
    doc = db.get(Document, document_id)
    if not doc or doc.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    vs.delete_by_document(db, document_id)

    file_path = _UPLOAD_DIR / doc.filename
    if file_path.exists():
        file_path.unlink(missing_ok=True)

    db.delete(doc)
    db.commit()


@router.get("/{document_id}/file")
def serve_document_file(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Stream the raw PDF file back to the client."""
    doc = db.get(Document, document_id)
    if not doc or doc.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = _UPLOAD_DIR / doc.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(str(file_path), media_type="application/pdf", filename=doc.original_name)
