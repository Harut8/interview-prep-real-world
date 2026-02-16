# Task 10: HTTP Client Wrapper — Fix Retry Logic & Add Circuit Breaker

**Time limit: 60 minutes**

## Existing Codebase
A wrapper around `httpx` for making HTTP requests with retry logic and error handling.

## Problems to Fix
1. Retry logic retries on ALL status codes including 400/422 (should only retry on 5xx and timeouts).
2. The retry delay is not actually exponential — it uses a fixed delay.
3. The `timeout` parameter is ignored in the actual request.
4. Response logging leaks sensitive headers (Authorization, Cookie).

## Features to Implement
1. Add a circuit breaker pattern: after N consecutive failures, stop making requests for M seconds, then allow one probe request.
2. Add request/response hooks: `on_request(method, url, headers)` and `on_response(status, elapsed)`.
3. Write tests using `httpx` mocking (respx or pytest-httpx).

## What We Evaluate
- HTTP error handling patterns
- Circuit breaker pattern
- Security awareness (header leaking)
- Proper use of httpx
