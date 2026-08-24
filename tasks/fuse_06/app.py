import time
import threading
from typing import Protocol


class RateLimiter(Protocol):
    def allow(self, key: str) -> bool: ...
    def remaining(self, key: str) -> int: ...


class TokenBucketLimiter:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        pass

    def allow(self, key: str) -> bool:
        raise NotImplementedError

    def remaining(self, key: str) -> int:
        raise NotImplementedError


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        pass

    def allow(self, key: str) -> bool:
        raise NotImplementedError

    def remaining(self, key: str) -> int:
        raise NotImplementedError
