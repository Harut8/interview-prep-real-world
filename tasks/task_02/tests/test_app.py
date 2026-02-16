import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_register_success(client):
    resp = client.post("/register", json={"username": "alice", "password": "Pass123!"})
    assert resp.status_code == 201


def test_register_duplicate(client):
    client.post("/register", json={"username": "bob", "password": "Pass123!"})
    resp = client.post("/register", json={"username": "bob", "password": "Pass123!"})
    assert resp.status_code == 409


def test_login_success(client):
    client.post("/register", json={"username": "carol", "password": "Pass123!"})
    resp = client.post("/login", json={"username": "carol", "password": "Pass123!"})
    assert resp.status_code == 200
    assert "token" in resp.get_json()


def test_login_wrong_password(client):
    client.post("/register", json={"username": "dave", "password": "Pass123!"})
    resp = client.post("/login", json={"username": "dave", "password": "wrong"})
    assert resp.status_code == 401


# TODO: Add test that verifies passwords are hashed (not stored plain-text)
# TODO: Add test for SQL injection prevention
# TODO: Add test that token expires
# TODO: Add tests for /refresh endpoint
# TODO: Add test for /protected with valid/invalid/expired token
