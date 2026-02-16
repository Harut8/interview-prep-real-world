# Task 08: Key-Value Store with TTL — Fix Expiration Logic & Add Persistence

**Time limit: 60 minutes**

## Existing Codebase
An in-memory key-value store with TTL (time-to-live) support, similar to a simplified Redis.

## Problems to Fix
1. Expired keys are not cleaned up — they're returned if accessed before cleanup runs.
2. The `set` method doesn't update TTL when overwriting an existing key.
3. The `keys()` method returns expired keys.
4. The `__len__` method counts expired entries.

## Features to Implement
1. Add `persist(filepath)` and `load(filepath)` methods to save/restore the store to/from a JSON file (handle TTL correctly — skip expired entries on load).
2. Add `get_or_set(key, default_factory, ttl)` — return existing value or compute and store a new one.
3. Write tests covering expiration edge cases.

## What We Evaluate
- Time-based logic correctness
- File I/O
- Context manager patterns
- Testing time-dependent code
