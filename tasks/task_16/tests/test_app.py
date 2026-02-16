import os
import pytest
from fastapi.testclient import TestClient
from app import app, DB_PATH


@pytest.fixture(autouse=True)
def clean_db():
    test_db = "test_products.db"
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
def sample_products(client):
    products = [
        {"name": "Laptop", "category": "electronics", "price": 999.99},
        {"name": "Mouse", "category": "electronics", "price": 29.99},
        {"name": "Keyboard", "category": "electronics", "price": 79.99},
        {"name": "Book", "category": "books", "price": 15.00},
        {"name": "Pen", "category": "office", "price": 2.50},
    ]
    for p in products:
        client.post("/products", json=p)
    return products


def test_list_all(client, sample_products):
    resp = client.get("/products")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5


def test_filter_by_category(client, sample_products):
    resp = client.get("/products?category=electronics")
    assert resp.json()["total"] == 3


# Tests price range — check exclusive upper bound behavior
def test_filter_by_price_range(client, sample_products):
    resp = client.get("/products?min_price=10&max_price=100")
    items = resp.json()["items"]
    for item in items:
        assert item["price"] >= 10
        assert item["price"] < 100  # exclusive upper bound


def test_pagination(client, sample_products):
    resp = client.get("/products?page=1&page_size=2")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["has_next"] is True
    assert data["page"] == 1


# TODO: Add tests for multi-field sorting
# TODO: Add tests for sparse fieldsets
# TODO: Add test for SQL injection prevention in sort parameter
