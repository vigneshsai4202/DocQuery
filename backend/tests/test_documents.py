import io
from unittest.mock import patch


def _make_pdf_bytes() -> bytes:
    """Minimal valid-looking PDF bytes for upload tests."""
    return b"%PDF-1.4 fake pdf content for testing purposes only"


def test_upload_wrong_extension(auth_client):
    client, _ = auth_client
    resp = client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_too_large(auth_client):
    client, _ = auth_client
    big = io.BytesIO(b"x" * (21 * 1024 * 1024))
    resp = client.post(
        "/api/v1/documents",
        files={"file": ("big.pdf", big, "application/pdf")},
    )
    assert resp.status_code == 413


def test_upload_happy_path(auth_client, tmp_path):
    client, _ = auth_client
    with patch("app.api.documents._run_ingestion"):
        resp = client.post(
            "/api/v1/documents",
            files={"file": ("sample.pdf", io.BytesIO(_make_pdf_bytes()), "application/pdf")},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["original_name"] == "sample.pdf"
    assert data["status"] == "pending"


def test_list_documents(auth_client):
    client, _ = auth_client
    with patch("app.api.documents._run_ingestion"):
        client.post(
            "/api/v1/documents",
            files={"file": ("list_test.pdf", io.BytesIO(_make_pdf_bytes()), "application/pdf")},
        )
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_delete_document(auth_client):
    client, _ = auth_client
    with patch("app.api.documents._run_ingestion"):
        upload_resp = client.post(
            "/api/v1/documents",
            files={"file": ("del_test.pdf", io.BytesIO(_make_pdf_bytes()), "application/pdf")},
        )
    doc_id = upload_resp.json()["id"]
    with patch("app.api.documents.vector_store") as mock_vs:
        mock_vs.return_value.delete_by_document = lambda x: None
        del_resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 204


def test_delete_not_found(auth_client):
    client, _ = auth_client
    resp = client.delete("/api/v1/documents/nonexistent-id")
    assert resp.status_code == 404
