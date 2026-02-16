import time
import json
from typing import Any, Callable


class TTLKeyValueStore:
    """In-memory key-value store with TTL support."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}  # key -> expiry timestamp

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a key-value pair with optional TTL in seconds."""
        self._data[key] = value
        if ttl is not None:
            self._expiry[key] = time.time() + ttl
        # BUG: if key already existed with TTL and new set() has no TTL,
        # the old TTL remains in self._expiry

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key. Returns default if not found or expired."""
        # BUG: doesn't check expiration before returning
        if key in self._data:
            return self._data[key]
        return default

    def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        if key in self._data:
            del self._data[key]
            self._expiry.pop(key, None)
            return True
        return False

    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key in self._expiry:
            return time.time() > self._expiry[key]
        return False

    def keys(self) -> list[str]:
        """Return all non-expired keys."""
        # BUG: returns ALL keys including expired ones
        return list(self._data.keys())

    def __len__(self) -> int:
        """Return count of non-expired keys."""
        # BUG: counts expired entries too
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        """Check if a non-expired key exists."""
        return key in self._data and not self._is_expired(key)

    def cleanup(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        expired = [k for k in self._expiry if self._is_expired(k)]
        for key in expired:
            del self._data[key]
            del self._expiry[key]
        return len(expired)


# TODO: Add persist(filepath) and load(filepath) methods
# TODO: Add get_or_set(key, default_factory, ttl) method
