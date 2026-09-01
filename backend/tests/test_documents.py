import io
from unittest.mock import patch


def _pdf():
    return io.BytesIO(b"%PDF-1.4 fake pdf content for testing purposes only")


def test_upload_requires_auth(client):
    resp = client.post(
        "/api/v1/documents",
        files={"file": ("test.pdf", _pdf(), "application/pdf")},
    )
    assert resp.status_code == 401


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


def test_upload_happy_path(auth_client):
    client, _ = auth_client
    with patch("app.api.documents._run_ingestion"):
        resp = client.post(
            "/api/v1/documents",
            files={"file": ("sample.pdf", _pdf(), "application/pdf")},
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
            files={"file": ("list_test.pdf", _pdf(), "application/pdf")},
        )
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_document(auth_client):
    client, _ = auth_client
    with patch("app.api.documents._run_ingestion"):
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("get_test.pdf", _pdf(), "application/pdf")},
        )
    doc_id = upload.json()["id"]
    resp = client.get(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


def test_delete_document(auth_client):
    client, _ = auth_client
    with patch("app.api.documents._run_ingestion"):
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("del_test.pdf", _pdf(), "application/pdf")},
        )
    doc_id = upload.json()["id"]
    with patch("app.api.documents.vs.delete_by_document"):
        resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 204


def test_delete_not_found(auth_client):
    client, _ = auth_client
    resp = client.delete("/api/v1/documents/nonexistent-id")
    assert resp.status_code == 404


def _signup_or_login(client, email, password="password123"):
    r = client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    if r.status_code == 400:
        r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def test_cannot_access_other_users_document(client):
    """Two users cannot see each other's documents."""
    token_a = _signup_or_login(client, "usera@example.com")
    client.headers.update({"Authorization": f"Bearer {token_a}"})
    with patch("app.api.documents._run_ingestion"):
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("private.pdf", _pdf(), "application/pdf")},
        )
    doc_id = upload.json()["id"]

    token_b = _signup_or_login(client, "userb@example.com")
    client.headers.update({"Authorization": f"Bearer {token_b}"})
    resp = client.get(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 404
