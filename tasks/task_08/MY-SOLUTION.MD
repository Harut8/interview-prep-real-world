EXAMPLE:
DATA = {key1: value1, key2: value2}
EXPIRY = {key1: 10, }

1. `set` — TTL overwrite bug
    - when ttl is None, must remove key from EXPIRY if it existed (clear old TTL)
    - when ttl is provided, overwrite the expiry timestamp
    - edge cases: ttl=0 means "expire immediately", negative ttl → reject or treat as instant expiry

2. `get` — check expiration before returning
    - call `_is_expired(key)` first, return default if expired
    - optionally: lazy cleanup — delete expired key from `_data` and `_expiry` on access (Redis-style)

3. `keys()` — filter out expired keys
    - `[k for k in self._data if not self._is_expired(k)]`

4. `__len__` — same filter as keys
    - `sum(1 for k in self._data if not self._is_expired(k))`

5. Persist and load — use stdlib `json`, NOT orjson
    - orjson is not in requirements.txt; `json` is already imported in app.py
    - JSON structure: `{"data": {...}, "expiry": {...}}`
    - on persist: only save non-expired entries
    - on load: skip entries whose expiry timestamp is in the past
    - handle file I/O errors (FileNotFoundError on load, etc.)

6. `get_or_set` — `dict.setdefault` does NOT work here
    - `setdefault` doesn't check expiration (expired key still "exists" in `_data`)
    - `setdefault` always evaluates the default — but `default_factory` is a callable that should only run when needed (lazy)
    - `setdefault` doesn't set TTL in `_expiry`
    - correct approach:
        ```
        def get_or_set(self, key, default_factory, ttl=None):
            if key in self._data and not self._is_expired(key):
                return self._data[key]
            value = default_factory()  # only called when missing/expired
            self.set(key, value, ttl)
            return value
        ```

7. Testability — `_is_expired` uses `time.time()` directly
    - same DI pattern as task 6: accept a `clock` callable in `__init__`
    - use `self._clock()` everywhere instead of `time.time()`
    - in tests, pass a fake clock to control time (avoids slow/flaky `time.sleep`)

8. `__contains__` (line 52-54) — checks expiration but doesn't clean up
    - expired key stays in `_data` and `_expiry` after the check
    - should lazily delete for consistency with `get`

9. Tests to write
    - expired key returns None / default
    - overwriting key with no TTL clears old TTL (key persists)
    - `keys()` and `len()` exclude expired entries
    - `get_or_set`: factory only called when key missing/expired
    - `get_or_set`: returns existing value without calling factory
    - persist/load round-trip: data survives, expired entries are skipped
    - persist/load with empty store
    - mock time via DI to avoid `time.sleep`