import time

from limiter import RateLimiter


def test_basic_limit():
    limiter = RateLimiter(capacity=5, refill_rate=1)
    # Use all tokens
    for _ in range(5):
        assert limiter.allow_request() is True
    # Next one should fail
    assert limiter.allow_request() is False


def test_refill():
    limiter = RateLimiter(capacity=2, refill_rate=10)
    assert limiter.allow_request() is True
    assert limiter.allow_request() is True
    assert limiter.allow_request() is False

    time.sleep(0.2)  # Should refill 2 tokens
    assert limiter.allow_request() is True
    assert limiter.allow_request() is True


def test_race_condition():
    # TASK: Implement a multi-threaded test that exposes the race condition
    # in the original 'limiter.py'.
    pass
