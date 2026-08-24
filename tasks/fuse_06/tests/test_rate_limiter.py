import pytest
import time
from app import TokenBucketLimiter, SlidingWindowLimiter


class TestTokenBucket:
    def test_allows_up_to_capacity(self):
        limiter = TokenBucketLimiter(capacity=3, refill_rate=0.0)
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False

    def test_remaining(self):
        limiter = TokenBucketLimiter(capacity=5, refill_rate=0.0)
        assert limiter.remaining("user1") == 5
        limiter.allow("user1")
        assert limiter.remaining("user1") == 4

    def test_refill(self):
        limiter = TokenBucketLimiter(capacity=2, refill_rate=100.0)
        limiter.allow("user1")
        limiter.allow("user1")
        assert limiter.allow("user1") is False
        time.sleep(0.05)  # 100 tokens/sec * 0.05s = 5 tokens, capped at 2
        assert limiter.allow("user1") is True

    def test_per_key_isolation(self):
        limiter = TokenBucketLimiter(capacity=1, refill_rate=0.0)
        assert limiter.allow("alice") is True
        assert limiter.allow("alice") is False
        assert limiter.allow("bob") is True

    def test_never_exceeds_capacity(self):
        limiter = TokenBucketLimiter(capacity=3, refill_rate=1000.0)
        time.sleep(0.05)
        assert limiter.remaining("user1") == 3


class TestSlidingWindow:
    def test_allows_up_to_max(self):
        limiter = SlidingWindowLimiter(max_requests=3, window_seconds=1.0)
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False

    def test_window_expires(self):
        limiter = SlidingWindowLimiter(max_requests=1, window_seconds=0.05)
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False
        time.sleep(0.06)
        assert limiter.allow("user1") is True

    def test_remaining(self):
        limiter = SlidingWindowLimiter(max_requests=5, window_seconds=1.0)
        assert limiter.remaining("user1") == 5
        limiter.allow("user1")
        assert limiter.remaining("user1") == 4

    def test_per_key_isolation(self):
        limiter = SlidingWindowLimiter(max_requests=1, window_seconds=1.0)
        assert limiter.allow("alice") is True
        assert limiter.allow("alice") is False
        assert limiter.allow("bob") is True
