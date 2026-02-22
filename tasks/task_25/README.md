# Task 25: Insert Delete GetRandom O(1) — Fix Bugs & Add Weighted Random

**Time limit: 60 minutes**

## Existing Codebase
A `RandomizedSet` data structure that supports insert, delete, and getRandom operations, all in average O(1) time. Uses a combination of a list and a hash map.

## Problems to Fix
1. The `remove` method doesn't swap with the last element before popping — it leaves a gap in the list, breaking O(1) random access.
2. The `get_random` method crashes on empty set instead of returning None or raising a clear error.
3. The `insert` method doesn't check for duplicates — allows the same value twice, corrupting the index map.
4. After removal, the index map retains stale entries for the swapped element's old position.

## Features to Implement
1. Add `get_random_weighted(weights)` — each element has an associated weight affecting random selection probability.
2. Add `bulk_insert(values)` and `bulk_remove(values)` for batch operations.
3. Add `get_random_n(n)` — returns n unique random elements.
4. Add `__iter__`, `__len__`, `__contains__` for Pythonic usage.
5. Add `snapshot()` and `restore(snapshot)` — save and restore the set state.
6. Write tests for all fixed bugs and new features.

## What We Evaluate
- O(1) time complexity for core operations
- Correct swap-and-pop deletion pattern
- Weighted random selection algorithm
- Test coverage and edge cases
