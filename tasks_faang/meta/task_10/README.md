# Task 10: Content Cache Service

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Content Cache Service. It implements multi-tier caching
(L1 fast / L2 shared) with intelligent invalidation, stale-while-revalidate
semantics, and metrics tracking.

## Existing Codebase

The `app.py` file contains a `ContentCacheService` that:
- Stores content with TTL-based expiration
- Supports multi-tier caching (L1 and L2)
- Implements stale-while-revalidate pattern
- Generates cache keys for content

## Known Bugs (3-4 to find and fix)

1. **Cache stampede (thundering herd)** — When a cache entry expires, all
   concurrent requests trigger a recomputation. There is no locking or
   deduplication to prevent multiple simultaneous recomputations.
2. **Stale-while-revalidate returns wrong version** — The stale-while-revalidate
   logic returns the revalidated (new) value instead of the stale value. It should
   immediately return the stale value and update in the background.
3. **Cache key collision** — The cache key function does not include the content
   type, so different content types with the same ID produce the same cache key.

## Features to Implement

1. **Cache Warming** — Pre-populate the cache with a batch of content items.
   Support specifying which tier(s) to warm.
2. **Per-key TTL** — Allow setting TTL per cache entry instead of using only the
   global default.
3. **Cache Hit Rate Metrics** — Track hits, misses, and stale-serves per tier.
   Calculate hit rate percentage.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
