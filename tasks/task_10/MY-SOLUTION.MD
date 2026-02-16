1. Timeout param not used (line 38-44)
    - pass `timeout=self.timeout` to `self._client.request()`
    - also set default on client constructor: `httpx.Client(base_url=base_url, timeout=timeout)`

2. Retry only on 5xx + 429, not all >= 400 (line 49)
    - change condition: `if response.status_code >= 500 or response.status_code == 429:`
    - 4xx (400, 422, 404) should NOT be retried — these are client errors, retrying won't help
    - for 429: ideally respect `Retry-After` header from server instead of own delay

3. Exponential backoff — both code paths (line 52 and line 61)
    - current code uses fixed `self.retry_delay` everywhere
    - fix: `time.sleep(self.retry_delay * (2 ** attempt) + random.uniform(0, 1))`
    - jitter (random) prevents thundering herd when many clients retry simultaneously
    - NOTE: the timeout retry path (line 61) has the same fixed delay bug

4. Sensitive header redaction (line 69-76)
    - define: `SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}`
    - replace values with `"[REDACTED]"` before logging
    - applies to BOTH request headers AND response headers (line 75 logs `response.headers`)
    - `Set-Cookie` in responses is also sensitive

5. Circuit breaker — custom implementation (no pybreaker)
    - 3 states: closed (normal), open (fail fast), half-open (probe)
    - params: `failure_threshold`, `reset_timeout`, `clock` (DI for testability)
    - flow:
        - closed: requests go through, track consecutive failures
        - if failures >= threshold → switch to open
        - open: immediately raise `CircuitOpenError`, no request made
        - after `reset_timeout` seconds → switch to half-open
        - half-open: allow one probe request
            - if probe succeeds → switch to closed, reset counter
            - if probe fails → switch back to open
    - only 5xx and TimeoutException count as failures (not 4xx)

6. Request/response hooks — custom implementation, NOT httpx event_hooks
    - task wants you to implement the hook pattern yourself
    - store hooks in `__init__`: `self._request_hooks: list[Callable]`, `self._response_hooks: list[Callable]`
    - provide `add_request_hook(fn)` and `add_response_hook(fn)` methods
    - in `request()`:
        - before HTTP call: `for hook in self._request_hooks: hook(method, url, headers)`
        - after HTTP call: `for hook in self._response_hooks: hook(response.status_code, elapsed)`
    - measure elapsed with `time.perf_counter()` before/after the call

7. Dead code on line 64-65
    - `except httpx.HTTPStatusError as e: raise`
    - this only fires when `raise_for_status()` is called (line 54), which only happens on last attempt
    - the catch just re-raises — it does nothing useful, remove it

8. Tests — use `respx` or `pytest-httpx` for HTTP mocking
    - successful request returns response
    - 5xx triggers retry with exponential delay (mock `time.sleep` to verify increasing delays)
    - 4xx (400, 422) is NOT retried, raises immediately
    - 429 is retried
    - timeout is applied to requests
    - sensitive headers are NOT present in log output (capture log with `caplog` fixture)
    - circuit breaker opens after N consecutive 5xx failures
    - circuit breaker rejects requests while open (raises immediately)
    - circuit breaker allows probe after cooldown, closes on success
    - request/response hooks are called with correct arguments
    - context manager (`with`) properly closes client