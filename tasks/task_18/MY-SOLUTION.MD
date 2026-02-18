1. Middleware validation in `add()` (line 41-42)
    - `if not isinstance(middleware, Middleware): raise TypeError(...)`
    - test expects `TypeError` on invalid input

2. Fix ordering (line 59) — remove `reversed()`
    - change `for mw in reversed(self.middlewares)` to `for mw in self.middlewares`
    - first added should run first

3. Exception in `process_request` — must run response chain for already-executed middlewares
    - can't just stop processing — cleanup middlewares (e.g. timing, logging) need to run
    - create error response (500) and pass through `process_response` for `executed_middlewares`
    - then re-raise the exception

4. Exception in handler (line 69) — run response chain, then re-raise
    - the test (line 65) expects the exception to propagate, but cleanup must run first
    ```
    try:
        response = self._handler(processed_request)
    except Exception:
        response = Response(status_code=500)
        for mw in reversed(executed_middlewares):
            mw.process_response(processed_request, response)
        raise  # re-raise after cleanup
    ```

5. Short-circuit skips response chain (lines 61-63)
    - when a middleware returns a Response (e.g. AuthMiddleware returns 401),
      it returns directly WITHOUT running `process_response` on already-executed middlewares
    - fix: on short-circuit, still run `process_response` for `executed_middlewares`:
    ```
    if isinstance(result, Response):
        for mw in reversed(executed_middlewares):
            result = mw.process_response(processed_request, result)
        return result
    ```

6. Mutable shared state — defensive copy of request
    - use `copy.deepcopy(request)` or a custom `copy()` method
    - shallow copy is not enough — `headers` dict would still be shared
    ```
    def copy(self):
        return Request(method=self.method, path=self.path,
                       headers=dict(self.headers), body=self.body)
    ```
    - pass a copy to each middleware so one can't corrupt state for others

7. `set_handler` has no validation
    - passing non-callable doesn't fail until `handle()` is called
    - fix: `if not callable(handler): raise TypeError(...)`

---

TimingMiddleware:
- process_request: record start time
- process_response: calculate duration, add `X-Process-Time` to response headers
- NOTE: storing `self.start_time` works for single-threaded, but not concurrent requests
    - alternative: store start time on the request object or use `threading.local()`

AuthMiddleware:
- process_request: check for API key in headers
    - if missing/invalid: return `Response(status_code=401)` to short-circuit (not raise exception)
    - the chain already handles short-circuit on line 61-63
- process_response: no-op

LoggingMiddleware:
- process_request: log request method, path, and headers (mask auth headers)
- process_response: log response status code, duration, and headers (mask auth headers)

---

Tests to write:
- middleware executes in add order
- handler exception still runs `process_response` for all executed middlewares
- `process_request` exception still runs `process_response` for already-executed middlewares
- short-circuit (401) still runs `process_response` for earlier middlewares
- `add("not a middleware")` raises TypeError
- TimingMiddleware adds timing header to response
- AuthMiddleware returns 401 on missing key, passes on valid key
- LoggingMiddleware masks sensitive headers in logs
- request mutation in one middleware doesn't affect others (if using copies)
- `set_handler` with non-callable raises TypeError
