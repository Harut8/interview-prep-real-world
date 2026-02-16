import threading
from collections import OrderedDict
from typing import Any
from functools import wraps


class LRUCache:
    """Least Recently Used cache."""

    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._hits = 0
        self._misses = 0
        # Lock exists but is not used consistently
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Get value from cache. Returns None if not found."""
        if key in self._cache:
            self._hits += 1
            # BUG: doesn't move to end (update access order)
            # Should call self._cache.move_to_end(key)
            return self._cache[key]
        # BUG: doesn't increment misses
        return None

    def put(self, key: str, value: Any) -> None:
        """Put a value in the cache. Evicts LRU item if at capacity."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            if len(self._cache) >= self.capacity:
                self._cache.popitem(last=False)  # Remove oldest
            self._cache[key] = value

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def cache_info(self) -> dict:
        """Return cache statistics."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "capacity": self.capacity,
        }


def lru_cache(capacity: int = 128):
    """Decorator that adds LRU caching to a function."""
    def decorator(func):
        cache = LRUCache(capacity)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # BUG: crashes on unhashable arguments (lists, dicts)
            key = str((args, tuple(sorted(kwargs.items()))))
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.put(key, result)
            return result

        wrapper.cache = cache
        wrapper.cache_info = cache.cache_info
        wrapper.cache_clear = cache.clear
        return wrapper
    return decorator


# TODO: Add max_size_bytes eviction
# TODO: Add typed=True option to decorator
