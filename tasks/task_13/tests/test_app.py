import pytest
from app import LRUCache, lru_cache


def test_basic_get_put():
    cache = LRUCache(capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    assert cache.get("b") == 2


def test_eviction_at_capacity():
    cache = LRUCache(capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)  # should evict "a"
    assert cache.get("a") is None
    assert cache.get("c") == 3


# FAILS — fix LRU order (get should update access time)
def test_lru_eviction_order():
    cache = LRUCache(capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")  # access "a" — should make "b" the LRU
    cache.put("c", 3)  # should evict "b", not "a"
    assert cache.get("a") == 1  # "a" should still be there
    assert cache.get("b") is None  # "b" should be evicted


# FAILS — fix miss counter
def test_cache_info_misses():
    cache = LRUCache(capacity=2)
    cache.get("nonexistent")
    cache.get("also_missing")
    info = cache.cache_info()
    assert info["misses"] == 2


# FAILS — fix unhashable args handling
def test_decorator_with_list_args():
    @lru_cache(capacity=10)
    def process(items):
        return sum(items)

    result = process([1, 2, 3])
    assert result == 6


# TODO: Add thread safety tests
# TODO: Add tests for max_size_bytes eviction
# TODO: Add tests for typed=True option
