1. Thread safety — all methods need `with self._lock`
    - `get`, `put`, `delete`, `clear` all access `_cache`, `_hits`, `_misses`
    - `_hits += 1` is not atomic (read-modify-write) — counts lost under concurrency
    - `clear()` does 3 operations (clear, hits=0, misses=0) — needs to be atomic
    - lock already exists (line 16) but is never used

2. LRU order — `get` doesn't update access order (line 20-24)
    - add `self._cache.move_to_end(key)` before returning the value
    - without this, it's FIFO not LRU

3. Miss counter — never incremented (line 26)
    - add `self._misses += 1` before `return None`

4. Unhashable arguments (line 69)
    - `str()` approach actually works for most cases — `str` can convert anything
    - but `str` representation is fragile/ambiguous as a cache key
    - `sorted(kwargs.items())` can fail if values aren't comparable (mixed types)
    - better fix: use `repr()` (more deterministic) or `pickle.dumps((args, kwargs))`
    - or catch `TypeError` and skip caching for unhashable args

5. Cached `None` values bug (lines 70-72) — biggest functional bug
    - if a function returns `None`, the decorator treats it as cache miss every time:
        ```
        result = cache.get(key)
        if result is not None:  # BUG: None is a valid return value
            return result
        ```
    - fix: use a sentinel value:
        ```
        _MISSING = object()

        def get(self, key, default=_MISSING):
            if key in self._cache:
                ...
                return self._cache[key]
            self._misses += 1
            return default

        # in decorator:
        result = cache.get(key, _MISSING)
        if result is not _MISSING:
            return result
        ```

6. `typed=True` option — include type info in cache key
    - when enabled, `f(1)` and `f(1.0)` cached separately
    - include `tuple(type(a).__name__ for a in args)` in the key
    - NOTE: current `str()` approach already produces different strings for `1` vs `1.0`,
      so this mainly matters if switching to a hash-based key

7. Max memory size eviction — `LRUCache(max_size_bytes=N)`
    - track total memory: `sys.getsizeof(key) + sys.getsizeof(value)` per entry
    - on `put`: evict LRU entries until total memory under `max_size_bytes`
    - maintain running `_current_size` counter, update on put/delete/evict
    - `sys.getsizeof` is **shallow** — doesn't measure nested objects (list of dicts
      reports size of the list object, not contained dicts). Worth noting limitation.
    - for deep size: `sum(sys.getsizeof(x) for x in obj)` recursively, but expensive

8. Decorator doesn't expose `delete` (lines 77-79)
    - `cache_info` and `cache_clear` are exposed, but not `delete`
    - consider adding `wrapper.cache_delete = cache.delete`

9. Tests to write
    - LRU eviction order: access "a", then put "c" → "b" evicted, not "a"
    - miss counter: N misses → `cache_info()["misses"] == N`
    - unhashable args: `process([1,2,3])` doesn't crash
    - cached `None`: function returning `None` is cached (not re-called)
    - thread safety: spawn N threads doing get/put, assert no corruption
    - `typed=True`: `f(1)` and `f(1.0)` produce separate cache entries
    - max memory: evicts LRU entries when exceeding byte limit
    - `clear()`: resets all stats atomically
    - capacity: cache never exceeds specified capacity