import sqlite3
from contextlib import contextmanager
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

app = FastAPI()
DB_PATH = "products.db"


class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    in_stock: bool = True


class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    in_stock: bool


class PaginatedResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                in_stock BOOLEAN DEFAULT 1
            )
        """)
        conn.commit()


init_db()


@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO products (name, category, price, in_stock) VALUES (?, ?, ?, ?)",
            (product.name, product.category, product.price, product.in_stock),
        )
        conn.commit()
        return ProductResponse(id=cursor.lastrowid, **product.model_dump())


@app.get("/products", response_model=PaginatedResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
):
    with get_db() as conn:
        # Build WHERE clause
        conditions = []
        params = []

        if category:
            conditions.append("category = ?")
            params.append(category)
        if min_price is not None:
            conditions.append("price >= ?")
            params.append(min_price)
        if max_price is not None:
            # BUG: should be exclusive upper bound (<) but uses inclusive (<=)
            conditions.append("price <= ?")
            params.append(max_price)
        if in_stock is not None:
            conditions.append("in_stock = ?")
            params.append(in_stock)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        # BUG: runs a separate COUNT query every time
        count_cursor = conn.execute(f"SELECT COUNT(*) FROM products {where}", params)
        total = count_cursor.fetchone()[0]

        # BUG: same offset pagination issue as before
        offset = (page - 1) * page_size
        query = f"SELECT * FROM products {where} ORDER BY id LIMIT ? OFFSET ?"
        cursor = conn.execute(query, params + [page_size, offset])
        rows = cursor.fetchall()

        items = [ProductResponse(**dict(row)) for row in rows]
        has_next = (page * page_size) < total

        return PaginatedResponse(
            items=items, total=total, page=page,
            page_size=page_size, has_next=has_next,
        )


# TODO: Add multi-field sorting: ?sort=price:asc,name:desc
# TODO: Add sparse fieldsets: ?fields=id,name,price
