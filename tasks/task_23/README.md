# Task 23: Design Hit Counter — Fix Bugs & Add Sliding Window

**Time limit: 60 minutes**

## Existing Codebase
A hit counter that records hits and returns the number of hits in the past 5 minutes (300 seconds). Supports concurrent recording from multiple sources.

## Problems to Fix
1. The `hit` method doesn't handle out-of-order timestamps — a late-arriving hit with an older timestamp is silently ignored.
2. The `get_hits` method scans all stored hits instead of using an efficient sliding window.
3. The `_cleanup` method has an off-by-one error — it removes hits that are exactly 300 seconds old (they should still count).
4. Thread safety is missing — concurrent `hit()` calls can cause data races.

## Features to Implement
1. Add configurable window size (default 300 seconds).
2. Add `get_hits_per_second(timestamp)` — returns the hit rate (hits/sec) for the current window.
3. Add `get_hit_breakdown(timestamp, bucket_size)` — returns a dict of `{bucket_start: count}` for analysis.
4. Add `merge(other_counter)` — combines hits from another HitCounter instance (for distributed aggregation).
5. Add `top_sources(timestamp, n)` — returns the top N sources by hit count in the current window.
6. Write tests for all fixed bugs and new features.

## What We Evaluate
- Efficient time-based data structure (circular buffer or bucket array)
- Thread safety
- Sliding window implementation
- Edge case handling with timestamps
- Test coverage
