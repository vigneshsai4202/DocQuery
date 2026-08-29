import numpy as np
from unittest.mock import MagicMock, patch


def _mock_rag(answer="Test answer", sources=None):
    """Patch answer_question to return a canned response."""
    if sources is None:
        sources = []
    return patch("app.api.query.answer_question", return_value=(answer, sources))


def _mock_retrieve(results=None):
    if results is None:
        results = []
    return patch("app.api.query.retrieve_chunks", return_value=results)


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
        r2 = client.post("/api/v1/query/ask", json={"question": "Follow-up?", "conversation_id": conv_id})
    assert r2.status_code == 200
    assert r2.json()["conversation_id"] == conv_id


def test_ask_invalid_conversation_id(auth_client):
    client, _ = auth_client
    with _mock_rag():
        resp = client.post(
            "/api/v1/query/ask",
            json={"question": "Question?", "conversation_id": "nonexistent-id"},
        )
    assert resp.status_code == 404


def test_semantic_search_endpoint(auth_client):
    client, _ = auth_client
    with _mock_retrieve([]):
        resp = client.post("/api/v1/query/search", json={"query": "test query", "top_k": 3})
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_ask_unauthenticated(client):
    """Without auth, ask still works (single-user mode)."""
    with _mock_rag():
        resp = client.post("/api/v1/query/ask", json={"question": "Who are you?"})
    assert resp.status_code == 200
