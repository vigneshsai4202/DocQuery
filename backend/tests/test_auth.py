def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_system_user_auto_created(client):
    """First request auto-creates the system user; documents endpoint should return 200."""
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 200


def test_me_unauthenticated(client):
    """Auth endpoints are removed; /auth/me should 404."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 404
