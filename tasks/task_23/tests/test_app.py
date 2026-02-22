import pytest
from app import HitCounter, WINDOW_SIZE


@pytest.fixture
def counter():
    return HitCounter()


def test_basic_hit(counter):
    counter.hit(1.0)
    assert counter.get_hits(1.0) == 1


def test_multiple_hits(counter):
    counter.hit(1.0)
    counter.hit(2.0)
    counter.hit(3.0)
    assert counter.get_hits(3.0) == 3


# FAILS — fix out-of-order timestamp handling
def test_out_of_order_hits(counter):
    counter.hit(3.0)
    counter.hit(1.0)  # older timestamp arrives late
    counter.hit(2.0)
    assert counter.get_hits(3.0) == 3


# FAILS — fix off-by-one in cleanup
def test_boundary_hit_included(counter):
    counter.hit(1.0)
    # Hit at exactly 300 seconds ago should still count
    assert counter.get_hits(1.0 + WINDOW_SIZE) == 1


def test_expired_hits_removed(counter):
    counter.hit(1.0)
    # Hit at 301 seconds ago should be removed
    assert counter.get_hits(1.0 + WINDOW_SIZE + 1) == 0


def test_window_sliding(counter):
    for i in range(10):
        counter.hit(float(i))

    # At t=305, only hits at t=5,6,7,8,9 should remain (5 hits)
    assert counter.get_hits(305.0) == 5


def test_source_tracking(counter):
    counter.hit(1.0, source="web")
    counter.hit(2.0, source="api")
    counter.hit(3.0, source="web")
    assert counter.get_hits(3.0) == 3


def test_reset(counter):
    counter.hit(1.0)
    counter.hit(2.0)
    counter.reset()
    assert counter.get_hits(2.0) == 0


# TODO: Add tests for configurable window size
# TODO: Add tests for get_hits_per_second
# TODO: Add tests for get_hit_breakdown
# TODO: Add tests for merge
# TODO: Add tests for top_sources
# TODO: Add tests for thread safety
