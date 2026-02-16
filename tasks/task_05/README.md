# Task 05: REST API for Book Library — Fix CRUD Bugs & Add Search

**Time limit: 60 minutes**

## Existing Codebase
A FastAPI CRUD application for managing a book library with SQLite storage.

## Problems to Fix
1. The `update_book` endpoint doesn't return 404 when the book doesn't exist — returns 500.
2. The `list_books` endpoint has N+1 query problem when loading authors.
3. The pagination is off-by-one: requesting page 1 with limit 10 skips the first book.
4. The `delete_book` endpoint doesn't check if the book exists before deleting.

## Features to Implement
1. Add `GET /books/search?q=term` — search books by title or author name (case-insensitive).
2. Add `GET /books/stats` — return total count, count per genre, average publication year.
3. Write tests for all bugs and new features.

## What We Evaluate
- Database query efficiency
- Pagination correctness
- Search implementation
- Error handling with proper HTTP status codes
