import os
import pytest
from fastapi.testclient import TestClient
from app import app, DB_PATH


@pytest.fixture(autouse=True)
def clean_db():
    """Use a fresh database for each test."""
    test_db = "test_library.db"
    import app as app_module
    app_module.DB_PATH = test_db
    app_module.init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_books(client):
    books = [
        {"title": "War and Peace", "author": "Tolstoy", "genre": "Fiction", "year": 1869},
        {"title": "Anna Karenina", "author": "Tolstoy", "genre": "Fiction", "year": 1877},
        {"title": "Crime and Punishment", "author": "Dostoevsky", "genre": "Fiction", "year": 1866},
        {"title": "The Master and Margarita", "author": "Bulgakov", "genre": "Fantasy", "year": 1967},
    ]
    created = []
    for book in books:
        resp = client.post("/books", json=book)
        created.append(resp.json())
    return created


def test_create_book(client):
    resp = client.post("/books", json={
        "title": "Test Book", "author": "Author", "genre": "Test", "year": 2024
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == "Test Book"


# FAILS — fix pagination off-by-one
def test_pagination_first_page(client, sample_books):
    resp = client.get("/books?page=1&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["title"] == "War and Peace"


# FAILS — fix update_book to return 404
def test_update_nonexistent_book(client):
    resp = client.put("/books/9999", json={
        "title": "X", "author": "Y", "genre": "Z", "year": 2000
    })
    assert resp.status_code == 404


# FAILS — fix delete_book to return 404
def test_delete_nonexistent_book(client):
    resp = client.delete("/books/9999")
    assert resp.status_code == 404


# TODO: Add tests for search endpoint
# TODO: Add tests for stats endpoint
