import pytest
import time
from app import KVStore


@pytest.fixture
def store():
    return KVStore(capacity=3)


class TestBasicOps:
    def test_put_and_get(self, store):
        store.put("a", 1)
        assert store.get("a") == 1

    def test_overwrite(self, store):
        store.put("a", 1)
        store.put("a", 2)
        assert store.get("a") == 2

    def test_get_missing(self, store):
        assert store.get("x") is None

    def test_delete(self, store):
        store.put("a", 1)
        assert store.delete("a") is True
        assert store.get("a") is None

    def test_delete_missing(self, store):
        assert store.delete("x") is False

    def test_size(self, store):
        store.put("a", 1)
        store.put("b", 2)
        assert store.size() == 2

    def test_keys(self, store):
        store.put("a", 1)
        store.put("b", 2)
        assert set(store.keys()) == {"a", "b"}


class TestLRUEviction:
    def test_evicts_lru(self, store):
        store.put("a", 1)
        store.put("b", 2)
        store.put("c", 3)
        store.put("d", 4)  # evicts "a"
        assert store.get("a") is None
        assert store.get("d") == 4

    def test_access_refreshes_lru(self, store):
        store.put("a", 1)
        store.put("b", 2)
        store.put("c", 3)
        store.get("a")     # refresh "a"
        store.put("d", 4)  # evicts "b" (now LRU)
        assert store.get("a") == 1
        assert store.get("b") is None

    def test_put_refreshes_lru(self, store):
        store.put("a", 1)
        store.put("b", 2)
        store.put("c", 3)
        store.put("a", 10)  # refresh "a"
        store.put("d", 4)   # evicts "b"
        assert store.get("a") == 10
        assert store.get("b") is None


class TestTTL:
    def test_entry_expires(self, store):
        store.put("a", 1, ttl=0.05)
        assert store.get("a") == 1
        time.sleep(0.06)
        assert store.get("a") is None

    def test_non_expired_stays(self, store):
        store.put("a", 1, ttl=10.0)
        assert store.get("a") == 1

    def test_expired_not_counted_in_size(self, store):
        store.put("a", 1, ttl=0.05)
        time.sleep(0.06)
        store.get("a")  # trigger lazy cleanup
        assert store.size() == 0

    def test_no_ttl_never_expires(self, store):
        store.put("a", 1)
        time.sleep(0.05)
        assert store.get("a") == 1
