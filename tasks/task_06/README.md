# Task 06: Rate Limiter — Fix Implementation & Add Sliding Window

**Time limit: 60 minutes**

## Existing Codebase
A rate limiter class used as middleware for a web service. Implements a fixed-window algorithm.

## Problems to Fix
1. The rate limiter is not thread-safe — fails under concurrent access.
2. The `is_allowed` method has an off-by-one error in counting.
3. The `cleanup` method modifies a dict while iterating over it (RuntimeError).
4. Timestamps use `time.time()` directly, making the code untestable.

## Features to Implement
1. Add a `SlidingWindowRateLimiter` that counts requests in a sliding window (not fixed intervals).
2. Add a decorator `@rate_limit(max_requests=10, window_seconds=60)` that can be applied to any function.
3. Write thorough tests including edge cases (boundary of window, concurrent access).

## What We Evaluate
- Thread safety
- Algorithm correctness
- Testability (dependency injection for time)
- Decorator patterns
