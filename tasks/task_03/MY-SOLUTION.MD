1. For http client creation and request we need use context manager to ensure proper resource cleanup
2. For async.gather error handling we need either use asyncio.wait or wrap each task in try/except block or use manual cancellation list or taskgroup or return_exceptions=True
3. For deduplication we need to use set or dict to store unique items over all sources
4. Rate limitimg is broken since with simple sleep we can't control number of requests per second, so we need to use either semaphore or client side rate limiting algorithm like leaky bucket
5. For exponential backoff we need to use either custom implementation like
sleep (2 ** attempt) + random jitter or use tenacity library
6. For TTL cache we need to use either custom implementation or use redis or memcached + eviction policy