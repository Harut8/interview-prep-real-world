# Task 16: REST API Pagination & Filtering — Fix Query Bugs & Add Sorting

**Time limit: 60 minutes**

## Existing Codebase
A FastAPI service for managing products with pagination and filtering capabilities.

## Problems to Fix
1. Cursor-based pagination returns duplicate items when new products are added between pages.
2. Filter chaining with `AND`/`OR` logic is broken — all filters use AND regardless.
3. The `count` query runs separately for every page request — expensive and unnecessary.
4. Filtering by price range is inclusive on both sides but the test expects exclusive upper bound.

## Features to Implement
1. Add multi-field sorting: `?sort=price:asc,name:desc`.
2. Add `fields` parameter for sparse fieldsets: `?fields=id,name,price` returns only those fields.
3. Write tests for all pagination edge cases.

## What We Evaluate
- SQL query construction
- Pagination patterns (offset vs cursor)
- API design
- Edge case handling
