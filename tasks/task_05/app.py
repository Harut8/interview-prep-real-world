import sqlite3
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()
DB_PATH = "library.db"


class BookCreate(BaseModel):
    title: str
    author: str
    genre: str
    year: int


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    genre: str
    year: int


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
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                genre TEXT NOT NULL,
                year INTEGER NOT NULL
            )
        """)
        conn.commit()


init_db()


@app.post("/books", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO books (title, author, genre, year) VALUES (?, ?, ?, ?)",
            (book.title, book.author, book.genre, book.year),
        )
        conn.commit()
        return BookResponse(
            id=cursor.lastrowid, title=book.title, author=book.author,
            genre=book.genre, year=book.year,
        )


@app.get("/books", response_model=list[BookResponse])
def list_books(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    with get_db() as conn:
        # BUG: off-by-one error in pagination
        offset = page * limit
        cursor = conn.execute(
            "SELECT * FROM books LIMIT ? OFFSET ?", (limit, offset)
        )
        rows = cursor.fetchall()
        return [BookResponse(**dict(row)) for row in rows]


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Book not found")
        return BookResponse(**dict(row))


@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookCreate):
    with get_db() as conn:
        # BUG: doesn't check if book exists — returns 500 or silently succeeds
        conn.execute(
            "UPDATE books SET title=?, author=?, genre=?, year=? WHERE id=?",
            (book.title, book.author, book.genre, book.year, book_id),
        )
        conn.commit()
        return BookResponse(
            id=book_id, title=book.title, author=book.author,
            genre=book.genre, year=book.year,
        )


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    with get_db() as conn:
        # BUG: doesn't check if book exists before deleting
        conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()


# TODO: Add GET /books/search?q=term
# TODO: Add GET /books/stats
