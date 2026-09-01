from unittest.mock import patch


def _mock_rag(answer="Test answer", sources=None):
    return patch("app.api.query.answer_question", return_value=(answer, sources or []))


def _mock_retrieve(results=None):
    return patch("app.api.query.retrieve_chunks", return_value=results or [])


def _mock_stream(answer="Streamed answer", sources=None):
    def _gen():
        yield answer
    return patch("app.api.query.stream_answer", return_value=(sources or [], _gen()))


def test_ask_requires_auth(client):
    resp = client.post("/api/v1/query/ask", json={"question": "Who are you?"})
    assert resp.status_code == 401


def test_ask_creates_conversation(auth_client):
    client, _ = auth_client
    with _mock_rag("The answer is 42."):
        resp = client.post("/api/v1/query/ask", json={"question": "What is the answer?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "The answer is 42."
    assert "conversation_id" in data
    assert "message_id" in data


def test_ask_appends_to_existing_conversation(auth_client):
    client, _ = auth_client
    with _mock_rag("First answer."):
        r1 = client.post("/api/v1/query/ask", json={"question": "First question?"})
    conv_id = r1.json()["conversation_id"]

    with _mock_rag("Second answer."):
        r2 = client.post("/api/v1/query/ask", json={
            "question": "Follow-up?",
            "conversation_id": conv_id,
        })
    assert r2.status_code == 200
    assert r2.json()["conversation_id"] == conv_id


def test_ask_invalid_conversation_id(auth_client):
    client, _ = auth_client
    with _mock_rag():
        resp = client.post("/api/v1/query/ask", json={
            "question": "Question?",
            "conversation_id": "nonexistent-id",
        })
    assert resp.status_code == 404


def test_semantic_search_requires_auth(client):
    resp = client.post("/api/v1/query/search", json={"query": "test", "top_k": 3})
    assert resp.status_code == 401


def test_semantic_search(auth_client):
    client, _ = auth_client
    with _mock_retrieve([]):
        resp = client.post("/api/v1/query/search", json={"query": "test query", "top_k": 3})
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_stream_requires_auth(client):
    resp = client.post("/api/v1/query/ask/stream", json={"question": "test"})
    assert resp.status_code == 401


def test_stream_answer(auth_client):
    client, _ = auth_client
    with _mock_stream("Hello world"):
        resp = client.post("/api/v1/query/ask/stream", json={"question": "What is this?"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "sources" in body
    assert "token" in body


def _signup_or_login(client, email, password="password123"):
    r = client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    if r.status_code == 400:
        r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def test_conversation_isolation(client):
    """User A cannot access User B's conversation."""
    token_a = _signup_or_login(client, "qa@example.com")
    client.headers.update({"Authorization": f"Bearer {token_a}"})
    with _mock_rag("answer"):
        conv_resp = client.post("/api/v1/query/ask", json={"question": "hello"})
    conv_id = conv_resp.json()["conversation_id"]

    token_b = _signup_or_login(client, "qb@example.com")
    client.headers.update({"Authorization": f"Bearer {token_b}"})
    with _mock_rag("answer"):
        resp = client.post("/api/v1/query/ask", json={"question": "hi", "conversation_id": conv_id})
    assert resp.status_code == 404
