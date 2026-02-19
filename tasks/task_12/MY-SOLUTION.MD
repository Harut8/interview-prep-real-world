1. Semaphore for concurrency limit (line 51-54)
    - `asyncio.Semaphore(max_concurrent)` to cap parallel requests
    - acquire in `fetch_page` before making the request:
        ```
        sem = asyncio.Semaphore(10)
        async with sem:
            async with session.get(url) as resp: ...
        ```

2. `gather` with `return_exceptions=True` (line 54)
    - prevents one failure from losing all results
    - NOTE: current `fetch_page` already catches all exceptions (line 43-46) and returns
      `ScrapeResult(error=...)`, so `gather` won't actually fail as-is
    - still good defensive practice to add `return_exceptions=True`

3. Shared `aiohttp.ClientSession` — fix in aiohttp, NOT switch to httpx
    - code uses aiohttp (line 3) — don't suggest switching libraries
    - create one session in `scrape_all` and pass to all `fetch_page` calls:
        ```
        async def scrape_all(urls):
            async with aiohttp.ClientSession() as session:
                tasks = [fetch_page(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            return list(results)
        ```
    - change `fetch_page(url)` to `fetch_page(session, url)` — accept session as param

4. Blocking regex in `parse_page` (lines 20-23) — run in executor
    - `re.search` and `re.findall` on large HTML block the event loop
    - fix: offload to thread pool:
        ```
        title, links = await asyncio.get_event_loop().run_in_executor(
            None, parse_page, html, url
        )
        ```

5. Per-domain rate limiting — token bucket, NOT just semaphore
    - a semaphore limits concurrency (parallel requests), not rate (requests/second)
    - need a per-domain rate limiter with timestamp tracking:
        ```
        class DomainRateLimiter:
            def __init__(self, max_per_second):
                self._max = max_per_second
                self._timestamps = defaultdict(list)
                self._locks = defaultdict(asyncio.Lock)

            async def acquire(self, domain):
                async with self._locks[domain]:
                    now = time.time()
                    self._timestamps[domain] = [
                        t for t in self._timestamps[domain] if now - t < 1.0
                    ]
                    if len(self._timestamps[domain]) >= self._max:
                        sleep_time = 1.0 - (now - self._timestamps[domain][0])
                        await asyncio.sleep(sleep_time)
                    self._timestamps[domain].append(time.time())
        ```

6. Progress callback — use `asyncio.as_completed`
    - accept `on_progress: Callable[[int, int, str], None]` in `scrape_all`
    - use `as_completed` instead of `gather` to get results as they finish:
        ```
        completed = 0
        results = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            completed += 1
            results.append(result)
            if on_progress:
                on_progress(completed, len(urls), result.url)
        ```

7. Relative URLs ignored (lines 25-28)
    - `parse_page` only keeps absolute URLs, discards relative (`/page2`, `../other`)
    - `base_url` param exists but isn't used for resolution
    - fix: `urllib.parse.urljoin(base_url, link)` to resolve relative URLs

8. No timeout on `resp.text()` (line 38)
    - `ClientTimeout(total=10)` covers connection + headers
    - reading body could still hang on slow responses
    - consider separate read timeout or wrapping in `asyncio.wait_for`

9. Tests — use `pytest-asyncio` + `aioresponses`
    - mock HTTP responses (no real network calls)
    - shared session: verify only one session created for multiple URLs
    - semaphore: 100 URLs with limit=5, verify max 5 concurrent at any time
    - per-domain rate: 10 URLs same domain, verify requests spaced correctly
    - progress callback: verify called with correct (completed, total, url)
    - one URL fails: other results still returned
    - blocking regex: verify `parse_page` runs in executor (doesn't block loop)
    - relative URLs resolved correctly