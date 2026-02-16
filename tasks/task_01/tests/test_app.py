import pytest
from fastapi.testclient import TestClient
from app import app, url_storage


@pytest.fixture(autouse=True)
def clear_storage():
    url_storage.clear()
    yield
    url_storage.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_shorten_valid_url(client):
    response = client.post("/shorten", json={"url": "https://example.com"})
    assert response.status_code == 200
    data = response.json()
    assert "short_id" in data
    assert "short_url" in data


def test_redirect_existing(client):
    client.post("/shorten", json={"url": "https://example.com"})
    short_id = list(url_storage.keys())[0]
    response = client.get(f"/{short_id}", follow_redirects=False)
    assert response.status_code == 307


# This test SHOULD pass but currently FAILS — fix the bug
def test_redirect_nonexistent(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404


# This test SHOULD pass but currently FAILS — fix the bug
def test_shorten_empty_url(client):
    response = client.post("/shorten", json={"url": ""})
    assert response.status_code == 422


# This test SHOULD pass but currently FAILS — fix the bug
def test_shorten_invalid_url(client):
    response = client.post("/shorten", json={"url": "not-a-url"})
    assert response.status_code == 422


# TODO: Add tests for GET /stats/{short_id}
# TODO: Add tests for delete_url function
