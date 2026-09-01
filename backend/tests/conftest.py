import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, get_db
from app.main import app

# Disable rate limiting for tests
import app.api.auth as _auth_module
_auth_module.limiter.enabled = False

TEST_DB_URL = "sqlite:///:memory:"

_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(_engine, "connect")
def _set_sqlite_pragma(conn, _):
    conn.execute("PRAGMA foreign_keys=ON")

_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# pgvector Vector type is not available in SQLite — swap it for Text before table creation
import app.models.orm as _orm
if "embedding" in _orm.Chunk.__table__.c:
    _orm.Chunk.__table__.c["embedding"].type = Text()


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db():
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def _override_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """Sign up a test user and return (client, token)."""
    resp = client.post("/api/v1/auth/signup", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    if resp.status_code == 400:
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123",
        })
    assert resp.status_code in (200, 201), f"Auth failed: {resp.text}"
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, token
