import time
from collections import deque
from threading import Lock

class RateLimiter:
    """
    A simple Token Bucket rate limiter.
    BUG: This implementation has a subtle race condition and a logic error 
    in how tokens are replenished which allows for more requests than defined.
    """
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()

    def allow_request(self) -> bool:
        # BUG: Refill logic is simplistic and prone to drift
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add new tokens based on elapsed time
        new_tokens = elapsed * self.refill_rate
        if new_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

# TASK: Identify the race conditions and ensure thread-safety.
# TASK: Fix the precision issues and ensure the refill rate is strictly enforced.
# TASK: Write pytest cases to prove the bug and the fix.
