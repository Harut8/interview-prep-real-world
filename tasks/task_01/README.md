# Task 01: URL Shortener — Fix Bugs & Add Stats Endpoint

**Time limit: 60 minutes**

## Existing Codebase
You are given a FastAPI-based URL shortener service. Users can create short URLs and get redirected.

## Problems to Fix
1. The `POST /shorten` endpoint has a bug — it doesn't validate URLs properly (accepts empty strings and non-URL text).
2. The `GET /{short_id}` redirect endpoint returns 500 instead of 404 for non-existent short IDs.
3. The `delete_url` function has a bug — it doesn't actually delete from storage.

## Features to Implement
1. Add a `GET /stats/{short_id}` endpoint that returns JSON with:
   - `original_url`: the original URL
   - `created_at`: when it was created
   - `click_count`: how many times the redirect was used
2. Write pytest tests for all fixed bugs and the new endpoint.

## What We Evaluate
- Bug-finding and fixing ability
- Input validation
- Test coverage and quality
- Error handling
