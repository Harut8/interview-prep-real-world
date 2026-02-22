import pytest
from app import EventEmitter


@pytest.fixture
def emitter():
    return EventEmitter()


def test_on_and_emit(emitter):
    results = []
    emitter.on("test", lambda data: results.append(data))
    emitter.emit("test", "hello")
    assert results == ["hello"]


def test_multiple_listeners(emitter):
    results = []
    emitter.on("test", lambda d: results.append(f"a:{d}"))
    emitter.on("test", lambda d: results.append(f"b:{d}"))
    emitter.emit("test", "x")
    assert results == ["a:x", "b:x"]


# FAILS — fix: off should remove ALL occurrences of a listener
def test_off_removes_all_occurrences(emitter):
    results = []

    def listener(data):
        results.append(data)

    emitter.on("test", listener)
    emitter.on("test", listener)
    emitter.off("test", listener)
    emitter.emit("test", "x")
    assert results == []


# FAILS — fix: emit should not stop on listener exception
def test_emit_error_isolation(emitter):
    results = []

    def bad_listener(data):
        raise ValueError("oops")

    def good_listener(data):
        results.append(data)

    emitter.on("test", bad_listener)
    emitter.on("test", good_listener)
    emitter.emit("test", "x")
    assert results == ["x"]


# FAILS — fix: once listener should be removable by original reference
def test_once_fires_only_once(emitter):
    results = []

    def listener(data):
        results.append(data)

    emitter.once("test", listener)
    emitter.emit("test", "first")
    emitter.emit("test", "second")
    assert results == ["first"]


# FAILS — fix: listeners() should return a copy
def test_listeners_returns_copy(emitter):
    emitter.on("test", lambda: None)
    listeners = emitter.listeners("test")
    listeners.clear()  # mutate the returned list
    assert emitter.listener_count("test") == 1


def test_emit_nonexistent_event(emitter):
    assert emitter.emit("nonexistent") is False


def test_remove_all_listeners(emitter):
    emitter.on("a", lambda: None)
    emitter.on("b", lambda: None)
    emitter.remove_all_listeners()
    assert emitter.event_names() == []


def test_event_names(emitter):
    emitter.on("click", lambda: None)
    emitter.on("hover", lambda: None)
    assert set(emitter.event_names()) == {"click", "hover"}


def test_listener_count(emitter):
    emitter.on("test", lambda: None)
    emitter.on("test", lambda: None)
    assert emitter.listener_count("test") == 2


# TODO: Add tests for prepend_listener
# TODO: Add tests for wildcard "*" events
# TODO: Add tests for wait_for (async)
# TODO: Add tests for pipe
# TODO: Add tests for max listeners warning
