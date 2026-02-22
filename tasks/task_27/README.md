# Task 27: Interval List Intersections — Fix Bugs & Add Merge/Query Operations

**Time limit: 60 minutes**

## Existing Codebase
An interval list manager that supports finding intersections between two sorted lists of intervals, merging overlapping intervals, and querying point membership.

## Problems to Fix
1. The `find_intersections` method fails when one interval completely contains another — it only handles partial overlaps.
2. The `merge_intervals` method doesn't handle adjacent intervals (e.g., [1,3] and [3,5] should merge to [1,5]).
3. The `insert_interval` method doesn't maintain sorted order after insertion.
4. The `is_point_in_any` method uses linear scan — should use binary search for sorted intervals.

## Features to Implement
1. Add `subtract(intervals, to_remove)` — removes `to_remove` ranges from `intervals`, returning the remaining fragments.
2. Add `union(list_a, list_b)` — merges two sorted interval lists into one non-overlapping sorted list.
3. Add `gaps(intervals)` — returns the gaps (uncovered ranges) between intervals.
4. Add `IntervalTree` class for efficient point and range queries on large interval sets.
5. Add `total_coverage(intervals)` — returns the total length of all covered ranges.
6. Write tests for all fixed bugs and new features.

## What We Evaluate
- Two-pointer technique for interval intersection
- Merge/sort algorithms for intervals
- Binary search for efficient queries
- Edge case handling (empty lists, single-point intervals, adjacent intervals)
- Test coverage
