# In-Memory Key-Value Store with TTL + LRU Eviction

**Practical LLD — maps to LC 146 LRU Cache / LC 588 In-Memory File System.**

Implement a key-value store that supports time-to-live (TTL) expiration and LRU eviction.

## Interface

```python
class KVStore:
    def __init__(self, capacity: int) -> None: ...
    def put(self, key: str, value, ttl: float | None = None) -> None: ...
    def get(self, key: str) -> Any: ...
    def delete(self, key: str) -> bool: ...
    def size(self) -> int: ...
    def keys(self) -> list[str]: ...
```

## Requirements

- `put(key, value, ttl)` — stores a key-value pair. If `ttl` is given (in seconds), the entry expires after that duration.
- `get(key)` — returns the value, or `None` if missing/expired. Accessing a key refreshes its LRU position.
- `delete(key)` — removes and returns True, or False if not found.
- When the store exceeds `capacity`, evict the least-recently-used non-expired entry.
- Expired entries are lazily cleaned on access. Optionally support a `cleanup()` method.
- Thread-safe.

## Patterns Tested

Hash map + doubly-linked list (LRU), TTL/expiry logic, lazy vs eager cleanup, thread safety.

## Time Target: 45 minutes
