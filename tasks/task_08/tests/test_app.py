import pytest
import time
from app import TTLKeyValueStore


@pytest.fixture
def store():
    return TTLKeyValueStore()


def test_set_and_get(store):
    store.set("key1", "value1")
    assert store.get("key1") == "value1"


def test_get_missing_key(store):
    assert store.get("missing") is None
    assert store.get("missing", "default") == "default"


def test_delete(store):
    store.set("key1", "value1")
    assert store.delete("key1") is True
    assert store.get("key1") is None


# FAILS — fix get() to check expiration
def test_expired_key_returns_none(store):
    store.set("key1", "value1", ttl=1)
    time.sleep(1.1)
    assert store.get("key1") is None


# FAILS — fix keys() to exclude expired
def test_keys_excludes_expired(store):
    store.set("key1", "value1", ttl=1)
    store.set("key2", "value2")
    time.sleep(1.1)
    assert "key1" not in store.keys()
    assert "key2" in store.keys()


# FAILS — fix __len__ to exclude expired
def test_len_excludes_expired(store):
    store.set("key1", "value1", ttl=1)
    store.set("key2", "value2")
    time.sleep(1.1)
    assert len(store) == 1


# FAILS — fix set() TTL overwrite bug
def test_overwrite_removes_old_ttl(store):
    store.set("key1", "value1", ttl=1)
    store.set("key1", "value2")  # no TTL — should remove old TTL
    time.sleep(1.1)
    assert store.get("key1") == "value2"  # should NOT expire


# TODO: Add tests for persist/load
# TODO: Add tests for get_or_set
