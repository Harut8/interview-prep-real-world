# Task 13: LRU Cache — Fix Implementation & Add Size-Based Eviction

**Time limit: 60 minutes**

## Existing Codebase
A custom LRU (Least Recently Used) cache implementation with a decorator interface.

## Problems to Fix
1. The cache doesn't update access order on `get()` — it's actually FIFO, not LRU.
2. The `cache_info()` method returns wrong miss count (always 0).
3. The decorator doesn't work with unhashable arguments (lists, dicts) — crashes with TypeError.
4. Thread safety: concurrent access corrupts the internal linked list.

## Features to Implement
1. Add max memory size eviction: `LRUCache(max_size_bytes=1024*1024)` evicts entries when total memory exceeds limit. Use `sys.getsizeof` for estimation.
2. Add `@lru_cache` decorator with `typed=True` option — `f(1)` and `f(1.0)` should be cached separately.
3. Write tests for cache eviction order and memory limits.

## What We Evaluate
- Data structure knowledge (OrderedDict / doubly-linked list)
- Decorator patterns
- Thread safety
- Memory awareness
