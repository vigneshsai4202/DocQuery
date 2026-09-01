import pytest


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_signup(client):
    resp = client.post("/api/v1/auth/signup", json={
        "email": "signup_test@example.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_signup_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    client.post("/api/v1/auth/signup", json=payload)
    resp = client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_login_success(client):
    client.post("/api/v1/auth/signup", json={"email": "login@example.com", "password": "password123"})
    resp = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/v1/auth/signup", json={"email": "wrong@example.com", "password": "password123"})
    resp = client.post("/api/v1/auth/login", json={"email": "wrong@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401


def test_me_authenticated(auth_client):
    client, token = auth_client
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["email"] == "test@example.com"


def test_me_unauthenticated(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token(client):
    client.headers.update({"Authorization": "Bearer invalidtoken"})
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_protected_route_without_token(client):
    """Documents endpoint requires auth — should reject unauthenticated requests."""
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 401


def test_protected_route_with_token(auth_client):
    """After login, documents endpoint should be accessible."""
    client, _ = auth_client
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
