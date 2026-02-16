import pytest
from app import FixedWindowRateLimiter


def test_allows_under_limit():
    limiter = FixedWindowRateLimiter(max_requests=3, window_seconds=60)
    assert limiter.is_allowed("client1") is True
    assert limiter.is_allowed("client1") is True
    assert limiter.is_allowed("client1") is True


# FAILS due to off-by-one — fix is_allowed
def test_blocks_over_limit():
    limiter = FixedWindowRateLimiter(max_requests=2, window_seconds=60)
    assert limiter.is_allowed("client1") is True
    assert limiter.is_allowed("client1") is True
    assert limiter.is_allowed("client1") is False  # should be blocked


def test_different_clients_independent():
    limiter = FixedWindowRateLimiter(max_requests=1, window_seconds=60)
    assert limiter.is_allowed("client1") is True
    assert limiter.is_allowed("client2") is True


# FAILS — fix cleanup RuntimeError
def test_cleanup_doesnt_crash():
    limiter = FixedWindowRateLimiter(max_requests=5, window_seconds=0)
    limiter.is_allowed("client1")
    limiter.is_allowed("client2")
    import time
    time.sleep(0.1)
    limiter.cleanup()  # Should not raise RuntimeError


# TODO: Add thread safety tests
# TODO: Add tests for SlidingWindowRateLimiter
# TODO: Add tests for @rate_limit decorator
# TODO: Add tests with mocked time
