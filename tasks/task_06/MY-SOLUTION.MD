1. Thread safety bug in FixedWindowRateLimiter
    - at first if it is used in multi-threaded environment it can lead to race
    - so we need to add a single `threading.Lock` wrapping the entire `is_allowed` method body
    - one lock for the whole `requests` dict is simplest and sufficient here
    - this same lock also covers `self.requests[client_id]` access and `if client_id in self.requests`

2. Testability bug — time.time() used directly
    - the problem is **testability**, not accuracy
    - fix: dependency injection — accept a `clock` callable in __init__:
        `def __init__(self, max_requests, window_seconds, clock=time.time)`
    - use `self.clock()` everywhere instead of `time.time()`
    - in tests, pass a fake/mock clock to control time
    - NOTE: `get_remaining()` (line 33) also has the same bug — uses `time.time()` directly

3. Off-by-one in `is_allowed` (line 26)
    - `<=` allows max_requests + 1 requests, should be `<`

4. Dict modification during iteration in `cleanup` (line 45-50)
    - iterating over `self.requests` and deleting keys inside the loop causes RuntimeError
    - fix: snapshot the keys with `list(self.requests)` then iterate over that
    - no need for deep copy — `list()` on the dict gives a copy of keys only, which is enough

5. SlidingWindowRateLimiter
    - tracks individual request timestamps
    - always looks back exactly `window_seconds` from "now" (not fixed intervals)
    - on each `is_allowed` call: filter out timestamps older than `now - window_seconds`, count remaining
    - allows smoother rate limiting than fixed window (no burst at window boundary)

6. @rate_limit decorator — TODO (my own implementation)

7. Tests to write
    - mock time via DI to test window expiry without `time.sleep`
    - concurrent access: spawn threads calling `is_allowed` simultaneously, assert total allowed == max_requests
    - boundary: exactly max_requests should be allowed, max_requests+1 should be blocked
    - sliding window: requests spread across time, verify correct counting