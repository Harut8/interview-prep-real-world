import pytest
from app import EventEmitter


@pytest.fixture
def emitter():
    return EventEmitter()


def test_basic_emit(emitter):
    results = []
    emitter.on("test", lambda data: results.append(data))
    emitter.emit("test", "hello")
    assert results == ["hello"]


def test_multiple_handlers(emitter):
    results = []
    emitter.on("test", lambda d: results.append(f"a:{d}"))
    emitter.on("test", lambda d: results.append(f"b:{d}"))
    emitter.emit("test", "x")
    assert len(results) == 2


# FAILS — fix exception isolation
def test_handler_exception_doesnt_stop_others(emitter):
    results = []

    def bad_handler(data):
        raise ValueError("oops")

    emitter.on("test", bad_handler)
    emitter.on("test", lambda d: results.append(d))
    emitter.emit("test", "hello")
    assert results == ["hello"]


# FAILS — fix once() bug
def test_once_fires_only_once(emitter):
    count = [0]

    def handler(data):
        count[0] += 1

    emitter.once("test", handler)
    emitter.emit("test", "a")
    emitter.emit("test", "b")
    assert count[0] == 1


# FAILS — fix unsubscribe during emit
def test_unsubscribe_during_emit(emitter):
    results = []

    def self_removing_handler(data):
        results.append("removed")
        emitter.off("test", self_removing_handler)

    emitter.on("test", self_removing_handler)
    emitter.on("test", lambda d: results.append("kept"))
    emitter.emit("test", None)  # Should not crash
    assert "kept" in results


# TODO: Add tests for async handlers
# TODO: Add tests for event history
