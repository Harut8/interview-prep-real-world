# API Client with Retries + Exponential Backoff + Rate Limiting

**Practical LLD — directly reported Fuse interview prompt.**

Implement a resilient HTTP-like API client class that handles transient failures gracefully.

## Interface

```python
class APIClient:
    def __init__(self, base_url: str, max_retries: int = 3, rate_limit: int = 10) -> None: ...
    def get(self, endpoint: str) -> Response: ...
    def post(self, endpoint: str, body: dict) -> Response: ...

class Response:
    status: int
    body: dict
    retries_used: int
```

## Requirements

- **Retries**: On 5xx or connection error, retry up to `max_retries` times.
- **Exponential backoff**: Wait `2^attempt` seconds between retries (use a sleep function that can be injected for testing).
- **Rate limiting**: No more than `rate_limit` requests per second (use a token-bucket internally).
- **Timeout**: Individual requests time out after a configurable duration.
- **Circuit breaker** (extension): After N consecutive failures, stop trying for a cooldown period. Then allow one probe request.
- Non-retryable errors (4xx) should raise immediately, not retry.

## Patterns Tested

Strategy pattern, decorator/wrapper, dependency injection (for testing), state machine (circuit breaker).

## What You Should Do

1. Write tests using an injectable transport (mock the actual HTTP layer).
2. Build incrementally: basic requests → retries → backoff → rate limit → circuit breaker.

## Time Target: 50 minutes
