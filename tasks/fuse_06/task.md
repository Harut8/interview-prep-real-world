# Rate Limiter (Token Bucket + Sliding Window)

**Practical LLD — matches Fuse's "refactor API client with rate limiting" prompt.**

Implement two rate-limiting strategies as classes behind a common interface.

## Interface

```python
class RateLimiter(Protocol):
    def allow(self, key: str) -> bool: ...
    def remaining(self, key: str) -> int: ...

class TokenBucketLimiter:
    def __init__(self, capacity: int, refill_rate: float) -> None: ...
    def allow(self, key: str) -> bool: ...
    def remaining(self, key: str) -> int: ...

class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None: ...
    def allow(self, key: str) -> bool: ...
    def remaining(self, key: str) -> int: ...
```

## Requirements

### Token Bucket
- Each key gets a bucket with `capacity` tokens. Starts full.
- `allow()` consumes 1 token if available, returns True. Returns False if empty.
- Tokens refill at `refill_rate` tokens/second (fractional tokens accumulate).
- Never exceeds `capacity`.

### Sliding Window
- Each key tracks timestamps of recent requests.
- `allow()` returns True if fewer than `max_requests` occurred in the last `window_seconds`.
- Old entries are cleaned up.

### Both
- `remaining()` returns how many more requests would be allowed right now.
- Thread-safe.
- Per-key isolation (user "alice" doesn't affect user "bob").

## Patterns Tested

Strategy pattern, time-based logic, thread safety, interface conformance.

## Time Target: 45 minutes
