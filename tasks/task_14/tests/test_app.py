import pytest
from fastapi.testclient import TestClient
from app import app, sessions, generate_session_id


@pytest.fixture(autouse=True)
def clear_sessions():
    sessions.clear()
    yield
    sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_login(client):
    resp = client.post("/login", json={"username": "alice", "password": "password123"})
    assert resp.status_code == 200
    assert "session_id" in resp.json()


def test_login_invalid(client):
    resp = client.post("/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401


def test_get_me(client):
    resp = client.post("/login", json={"username": "alice", "password": "password123"})
    session_id = resp.json()["session_id"]
    client.cookies.set("session_id", session_id)
    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


# FAILS — fix to return 401 instead of 500
def test_get_me_with_deleted_session(client):
    resp = client.post("/login", json={"username": "alice", "password": "password123"})
    session_id = resp.json()["session_id"]
    sessions.clear()  # simulate session deletion
    client.cookies.set("session_id", session_id)
    resp = client.get("/me")
    assert resp.status_code == 401


# FAILS — fix session ID to be cryptographically secure
def test_session_id_is_secure():
    ids = {generate_session_id() for _ in range(1000)}
    # Should have high entropy — all unique, not sequential
    assert len(ids) == 1000
    # Should be at least 32 chars (hex string)
    for sid in ids:
        assert len(sid) >= 32


# TODO: Add tests for session expiration
# TODO: Add tests for sliding TTL
# TODO: Add tests for DELETE /sessions
# TODO: Add tests for session metadata
