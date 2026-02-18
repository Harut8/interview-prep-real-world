1. `close()` bug (line 32) — `self._closed = False` should be `self._closed = True`

2. Validate connection before handing out in `acquire()`
    - call `conn.ping()` after getting from pool
    - if dead: discard it, try next from pool or create new
    - loop until a healthy connection is found or pool exhausted

3. Timeout to prevent deadlock (line 85)
    - `self._pool.get()` blocks forever when all connections are in use
    - fix: `self._pool.get(timeout=self.acquire_timeout)`
    - catch `queue.Empty` and raise `TimeoutError("Could not acquire connection")`

4. Race condition in `acquire()` (lines 70-71)
    - `self._pool.empty()` check is not atomic with `self._pool.get_nowait()`
    - another thread can take the last connection between check and get → `queue.Empty`
    - fix: use try/except instead of checking empty:
        ```
        try:
            conn = self._pool.get_nowait()
        except queue.Empty:
            pass  # no connection available, try creating
        ```

5. Context manager — `@contextmanager` on a `connection()` method
    - guarantees `release()` is always called (fixes "callers forget to release" bug)
    ```
    @contextmanager
    def connection(self):
        conn = self.acquire()
        try:
            yield conn
        finally:
            self.release(conn)
    ```

6. `close_all()` — should WAIT for in-use connections, not force close
    - forcing close on active connections corrupts mid-query operations
    - fix: set a shutdown flag, wait for in-use connections to return (with timeout):
        ```
        def close_all(self, timeout=30):
            self._shutting_down = True
            deadline = time.time() + timeout
            while self._in_use and time.time() < deadline:
                time.sleep(0.1)
            while not self._pool.empty():
                conn = self._pool.get_nowait()
                conn.close()
        ```

7. `release()` doesn't validate ownership
    - can release a connection not from this pool, or release same connection twice
    - fix: check `conn.id in self._in_use` before releasing
    - raise `ValueError` if connection doesn't belong or was already released

8. Health check — pre-check before handing out (ping in acquire)
    - background thread periodic check is nice-to-have but out of scope

9. Stats — counters protected by `self._lock`
    - `get_stats()` returns: `total`, `available` (pool.qsize()), `in_use` (len(_in_use)),
      `created_total`, `errors_total`
    - all counter increments must be inside `self._lock` (no atomic integers in Python)
    - `_create_connection` (line 64) increments `_total_created` outside lock — bug if called
      from health check replacement path

10. Tests to write
    - `close()` sets `is_closed` to True
    - stale connection replaced with healthy one on acquire
    - acquire with timeout raises `TimeoutError` (not deadlock)
    - context manager releases connection even on exception
    - `close_all` waits for in-use connections before closing
    - `get_stats` returns correct counts
    - concurrent: spawn N threads acquiring/releasing, assert no crashes, all returned
    - double release raises error
    - releasing foreign connection raises error