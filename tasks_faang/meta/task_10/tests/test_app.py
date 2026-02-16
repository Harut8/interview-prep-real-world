"""Tests for Content Cache Service."""

import threading
import time
import pytest
from app import ContentCacheService, ContentType, CacheTier, CacheMetrics


@pytest.fixture
def cache() -> ContentCacheService:
    return ContentCacheService()


class TestCacheKeyCollision:
    def test_different_types_different_keys(self, cache: ContentCacheService):
        """FAILING: Different content types with same ID should have different keys.

        Bug: Cache key doesn't include content type.
        """
        cache.put("123", ContentType.POST, {"title": "My Post"})
        cache.put("123", ContentType.PROFILE, {"name": "Alice"})

        post = cache.get("123", ContentType.POST)
        profile = cache.get("123", ContentType.PROFILE)

        assert post == {"title": "My Post"}, f"Post overwritten by profile: {post}"
        assert profile == {"name": "Alice"}, f"Profile should be Alice: {profile}"

    def test_same_type_same_id(self, cache: ContentCacheService):
        """PASSING: Same type and ID should return cached value."""
        cache.put("456", ContentType.POST, "hello")
        result = cache.get("456", ContentType.POST)
        assert result == "hello"


class TestStaleWhileRevalidate:
    def test_returns_stale_value_during_revalidation(self, cache: ContentCacheService):
        """FAILING: Should return stale value immediately, not the revalidated one.

        Bug: Returns new value instead of stale value.
        """
        now = 1000.0
        cache.put("post_1", ContentType.POST, "version_1", ttl=60.0, now=now)

        # Time moves past TTL but within grace period
        fetch_time = now + 65.0  # 5 seconds past TTL, within 60s grace

        def fetcher():
            return "version_2"

        result = cache.get_stale_while_revalidate(
            "post_1", ContentType.POST, fetcher, now=fetch_time
        )
        assert result == "version_1", (
            f"Should return stale 'version_1' during revalidation, got '{result}'"
        )

    def test_revalidation_updates_cache(self, cache: ContentCacheService):
        """PASSING (after stale fix): After revalidation, cache should have new value."""
        now = 1000.0
        cache.put("post_1", ContentType.POST, "version_1", ttl=60.0, now=now)

        fetch_time = now + 65.0

        def fetcher():
            return "version_2"

        # First call returns stale
        cache.get_stale_while_revalidate(
            "post_1", ContentType.POST, fetcher, now=fetch_time
        )

        # After revalidation, cache should have the new value
        result = cache.get("post_1", ContentType.POST, now=fetch_time)
        assert result == "version_2"


class TestCacheStampede:
    def test_no_thundering_herd(self, cache: ContentCacheService):
        """FAILING: Concurrent cache misses should not all trigger fetcher.

        Bug: No locking — all threads call fetcher simultaneously.
        """
        fetch_count = {"count": 0}
        lock = threading.Lock()

        def slow_fetcher():
            with lock:
                fetch_count["count"] += 1
            time.sleep(0.1)  # Simulate slow computation
            return "expensive_result"

        results = []
        errors = []

        def concurrent_get():
            try:
                result = cache.get(
                    "hot_key", ContentType.POST, fetcher=slow_fetcher
                )
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=concurrent_get) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(r == "expensive_result" for r in results)
        # With stampede protection, fetcher should be called at most once
        assert fetch_count["count"] == 1, (
            f"Fetcher called {fetch_count['count']} times, expected 1 (stampede!)"
        )


class TestCacheExpiration:
    def test_expired_entry_returns_none(self, cache: ContentCacheService):
        """PASSING: Expired entry should return None if no fetcher."""
        now = 1000.0
        cache.put("p1", ContentType.POST, "value", ttl=10.0, now=now)
        result = cache.get("p1", ContentType.POST, now=now + 15.0)
        assert result is None

    def test_non_expired_returns_value(self, cache: ContentCacheService):
        """PASSING: Non-expired entry should return value."""
        now = 1000.0
        cache.put("p1", ContentType.POST, "value", ttl=10.0, now=now)
        result = cache.get("p1", ContentType.POST, now=now + 5.0)
        assert result == "value"


class TestCacheWarming:
    def test_warm_cache_populates_entries(self, cache: ContentCacheService):
        """TODO: Warming should populate cache with provided items."""
        items = [
            ("p1", ContentType.POST, "post data 1"),
            ("p2", ContentType.POST, "post data 2"),
            ("prof1", ContentType.PROFILE, "profile data"),
        ]
        count = cache.warm_cache(items)
        assert count == 3

        assert cache.get("p1", ContentType.POST) == "post data 1"
        assert cache.get("p2", ContentType.POST) == "post data 2"
        assert cache.get("prof1", ContentType.PROFILE) == "profile data"

    def test_warm_specific_tier(self, cache: ContentCacheService):
        """TODO: Warming specific tier should only populate that tier."""
        items = [("p1", ContentType.POST, "data")]
        cache.warm_cache(items, tiers=[CacheTier.L2])

        # L2 should have it
        key = cache._make_cache_key("p1", ContentType.POST)
        assert key in cache.l2_cache
        # L1 should NOT have it (only warmed L2)
        assert key not in cache.l1_cache


class TestPerKeyTTL:
    def test_custom_ttl_per_key(self, cache: ContentCacheService):
        """TODO: Different keys can have different TTLs."""
        now = 1000.0
        cache.put("short", ContentType.POST, "short-lived", ttl=5.0, now=now)
        cache.put("long", ContentType.POST, "long-lived", ttl=600.0, now=now)

        at_10 = now + 10.0
        assert cache.get("short", ContentType.POST, now=at_10) is None, (
            "Short TTL entry should be expired"
        )
        assert cache.get("long", ContentType.POST, now=at_10) == "long-lived", (
            "Long TTL entry should still be alive"
        )


class TestMetrics:
    def test_hit_miss_tracking(self, cache: ContentCacheService):
        """TODO: Cache should track hits and misses."""
        now = 1000.0
        cache.put("p1", ContentType.POST, "data", now=now)

        # Hit
        cache.get("p1", ContentType.POST, now=now + 1)
        # Miss
        cache.get("missing", ContentType.POST, now=now + 1)

        l1_metrics = cache.get_metrics(CacheTier.L1)
        assert l1_metrics.hits >= 1, f"Expected at least 1 hit, got {l1_metrics.hits}"
        assert l1_metrics.misses >= 1, f"Expected at least 1 miss, got {l1_metrics.misses}"

    def test_hit_rate_calculation(self, cache: ContentCacheService):
        """TODO: Hit rate should be calculated correctly."""
        now = 1000.0
        cache.put("p1", ContentType.POST, "data", now=now)

        # 3 hits
        for _ in range(3):
            cache.get("p1", ContentType.POST, now=now + 1)
        # 1 miss
        cache.get("missing", ContentType.POST, now=now + 1)

        rate = cache.get_hit_rate(CacheTier.L1)
        assert rate == pytest.approx(75.0, abs=1.0), (
            f"Expected ~75% hit rate (3/4), got {rate}%"
        )

    def test_stale_serve_tracked(self, cache: ContentCacheService):
        """TODO: Stale-while-revalidate serves should be tracked."""
        now = 1000.0
        cache.put("p1", ContentType.POST, "v1", ttl=10.0, now=now)

        # Trigger stale serve
        cache.get_stale_while_revalidate(
            "p1", ContentType.POST, lambda: "v2", now=now + 15.0
        )

        metrics = cache.get_metrics(CacheTier.L1)
        assert metrics.stale_serves >= 1
