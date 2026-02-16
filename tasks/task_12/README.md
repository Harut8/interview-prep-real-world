# Task 12: Async Web Scraper — Fix Resource Leaks & Add Rate Limiting

**Time limit: 60 minutes**

## Existing Codebase
An async web scraper using aiohttp that fetches multiple pages concurrently, parses content, and stores results.

## Problems to Fix
1. `aiohttp.ClientSession` is created per request instead of being shared (connection pool not utilized).
2. No concurrency limit — if given 1000 URLs, tries to open 1000 connections simultaneously.
3. The `parse_page` function uses a blocking regex operation on large HTML — should be run in executor.
4. Results are lost if any single URL fails (entire `gather` fails).

## Features to Implement
1. Add per-domain rate limiting: max N requests per second per domain.
2. Add a progress callback: `on_progress(completed: int, total: int, url: str)`.
3. Write tests with mocked HTTP responses.

## What We Evaluate
- Async resource management
- Concurrency control (semaphore)
- Error handling in concurrent code
- Proper aiohttp usage
