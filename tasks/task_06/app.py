import time
from collections import defaultdict
from functools import wraps
from typing import Callable


class FixedWindowRateLimiter:
    """Rate limiter using fixed time windows."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # BUG: no lock for thread safety
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """Check if a request from client_id is allowed."""
        now = time.time()  # BUG: direct time.time() makes testing hard
        window_start = now - self.window_seconds

        # Clean old entries for this client
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if ts > window_start
        ]

        # BUG: off-by-one, should be < not <=
        if len(self.requests[client_id]) <= self.max_requests:
            self.requests[client_id].append(now)
            return True
        return False

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for a client in current window."""
        now = time.time()
        window_start = now - self.window_seconds
        current_count = len(
            [ts for ts in self.requests[client_id] if ts > window_start]
        )
        return max(0, self.max_requests - current_count)

    def cleanup(self) -> None:
        """Remove expired entries from all clients."""
        now = time.time()
        window_start = now - self.window_seconds
        # BUG: modifying dict while iterating
        for client_id in self.requests:
            self.requests[client_id] = [
                ts for ts in self.requests[client_id] if ts > window_start
            ]
            if not self.requests[client_id]:
                del self.requests[client_id]

    def reset(self, client_id: str) -> None:
        """Reset rate limit for a specific client."""
        if client_id in self.requests:
            del self.requests[client_id]


# TODO: Implement SlidingWindowRateLimiter
# TODO: Implement @rate_limit decorator


class RateLimitExceeded(Exception):
    pass


def rate_limit(
    max_requests: int,
    window_seconds: int,
    limiter: FixedWindowRateLimiter | None = None,
):
    _rate_limiter = limiter or FixedWindowRateLimiter(
        max_requests, window_seconds
    )  # for testing

    def _rate_limit(func: Callable):
        @wraps(func)
        def wrapper(*args, client_id: str, **kwargs):
            if _rate_limiter.is_allowed(client_id):
                return func(*args, client_id=client_id, **kwargs)
            raise RateLimitExceeded(f"Rate limit exceeded for {client_id}")

        wrapper.limiter = _rate_limiter  # for testing
        return wrapper

    return _rate_limit
