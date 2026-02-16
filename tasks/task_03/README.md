# Task 03: Async Data Aggregator — Fix Concurrency Bugs & Add Caching

**Time limit: 60 minutes**

## Existing Codebase
An async service that fetches data from multiple external APIs in parallel and aggregates results.

## Problems to Fix
1. The `fetch_all` function uses `asyncio.gather` but doesn't handle individual failures — one failing source crashes everything.
2. There's a blocking `time.sleep` call inside an async function (blocks the event loop).
3. The `aggregate_results` function has O(n²) complexity — optimize it.
4. Resource leak: `aiohttp.ClientSession` is created but never properly closed.

## Features to Implement
1. Add an in-memory TTL cache so repeated requests within 60 seconds return cached results.
2. Add retry logic with exponential backoff (max 3 retries) for failed fetches.
3. Write tests using `pytest-asyncio` and mock the external API calls.

## What We Evaluate
- Async/await correctness
- Error handling in concurrent code
- Performance awareness
- Proper resource management
