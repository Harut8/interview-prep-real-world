"""
Content Cache Service
Multi-tier caching with invalidation, stale-while-revalidate, and metrics.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class CacheTier(Enum):
    L1 = "l1"  # Fast, local cache
    L2 = "l2"  # Shared cache


class ContentType(Enum):
    POST = "post"
    PROFILE = "profile"
    PHOTO = "photo"
    VIDEO = "video"
    COMMENT = "comment"


@dataclass
class CacheEntry:
    key: str
    value: Any
    content_type: ContentType
    created_at: float
    ttl: float  # seconds
    is_stale: bool = False

    @property
    def expires_at(self) -> float:
        return self.created_at + self.ttl

    def is_expired(self, now: float) -> bool:
        return now > self.expires_at


@dataclass
class CacheMetrics:
    hits: int = 0
    misses: int = 0
    stale_serves: int = 0

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100


class ContentCacheService:
    """Multi-tier content cache with stale-while-revalidate and metrics."""

    DEFAULT_TTL = 300.0  # 5 minutes
    STALE_GRACE_PERIOD = 60.0  # serve stale for 60 seconds while revalidating

    def __init__(self) -> None:
        self.l1_cache: dict[str, CacheEntry] = {}
        self.l2_cache: dict[str, CacheEntry] = {}
        self.metrics: dict[CacheTier, CacheMetrics] = {
            CacheTier.L1: CacheMetrics(),
            CacheTier.L2: CacheMetrics(),
        }
        self._revalidation_locks: dict[str, threading.Lock] = {}
        self._revalidating: set[str] = set()

    def _make_cache_key(self, content_id: str, content_type: ContentType) -> str:
        """Generate cache key.

        BUG: Does not include content_type in key. Different types with same ID
        produce the same key and overwrite each other.
        """
        # BUG: Missing content_type in key
        return f"cache:{content_id}"

    def get(self, content_id: str, content_type: ContentType,
            fetcher: Callable[[], Any] | None = None,
            now: float | None = None) -> Any | None:
        """Get content from cache, checking L1 then L2.

        If expired and fetcher provided, recomputes the value.
        BUG: No stampede protection — multiple concurrent gets all trigger fetcher.
        """
        current_time = now or time.time()
        key = self._make_cache_key(content_id, content_type)

        # Check L1
        entry = self.l1_cache.get(key)
        if entry and not entry.is_expired(current_time):
            return entry.value

        # Check L2
        entry = self.l2_cache.get(key)
        if entry and not entry.is_expired(current_time):
            # Promote to L1
            self.l1_cache[key] = entry
            return entry.value

        # Cache miss — recompute if fetcher provided
        # BUG: No locking — multiple threads all call fetcher simultaneously
        if fetcher:
            value = fetcher()
            self.put(content_id, content_type, value, now=current_time)
            return value

        return None

    def get_stale_while_revalidate(
        self,
        content_id: str,
        content_type: ContentType,
        fetcher: Callable[[], Any],
        now: float | None = None,
    ) -> Any | None:
        """Get content with stale-while-revalidate semantics.

        If entry is expired but within grace period:
        - Immediately return STALE value
        - Trigger background revalidation

        BUG: Returns the NEW (revalidated) value instead of the stale value.
        """
        current_time = now or time.time()
        key = self._make_cache_key(content_id, content_type)

        # Check L1 first
        entry = self.l1_cache.get(key)
        if entry is None:
            entry = self.l2_cache.get(key)

        if entry is None:
            # Full miss — fetch synchronously
            value = fetcher()
            self.put(content_id, content_type, value, now=current_time)
            return value

        if not entry.is_expired(current_time):
            return entry.value

        # Expired but within stale grace period?
        if current_time <= entry.expires_at + self.STALE_GRACE_PERIOD:
            stale_value = entry.value  # noqa: F841

            # BUG: Fetches synchronously and returns NEW value instead of stale
            new_value = fetcher()
            self.put(content_id, content_type, new_value, now=current_time)
            return new_value  # BUG: should return stale_value

        # Beyond grace period — full refresh
        value = fetcher()
        self.put(content_id, content_type, value, now=current_time)
        return value

    def put(self, content_id: str, content_type: ContentType,
            value: Any, ttl: float | None = None,
            now: float | None = None) -> None:
        """Put content into both cache tiers."""
        current_time = now or time.time()
        key = self._make_cache_key(content_id, content_type)
        effective_ttl = ttl if ttl is not None else self.DEFAULT_TTL

        entry = CacheEntry(
            key=key,
            value=value,
            content_type=content_type,
            created_at=current_time,
            ttl=effective_ttl,
        )
        self.l1_cache[key] = entry
        self.l2_cache[key] = entry

    def invalidate(self, content_id: str, content_type: ContentType) -> None:
        """Remove content from all cache tiers."""
        key = self._make_cache_key(content_id, content_type)
        self.l1_cache.pop(key, None)
        self.l2_cache.pop(key, None)

    def warm_cache(self, items: list[tuple[str, ContentType, Any]],
                   tiers: list[CacheTier] | None = None,
                   ttl: float | None = None) -> int:
        """Pre-populate cache with batch of items.

        items: list of (content_id, content_type, value)
        Returns number of items warmed.

        TODO: Implement cache warming.
        """
        return 0

    def get_metrics(self, tier: CacheTier) -> CacheMetrics:
        """Get cache metrics for a tier.

        TODO: Implement metrics tracking.
        """
        return self.metrics[tier]

    def get_hit_rate(self, tier: CacheTier) -> float:
        """Get hit rate percentage for a tier.

        TODO: Implement hit rate calculation.
        """
        return self.metrics[tier].hit_rate
