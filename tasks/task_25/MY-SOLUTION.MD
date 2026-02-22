# My Solution — Task 25

## Bug Fixes

### 1. `remove` doesn't swap with last element — breaks O(1)

Current code does `self._list.pop(idx)` which shifts all elements after `idx` — O(n). It also leaves `_index_map` stale for all shifted elements (bug #4).

Fix: classic **swap-and-pop** pattern. Swap the target with the last element, update the swapped element's index, then pop the last.

```python
def remove(self, val: int) -> bool:
    if val not in self._index_map:
        return False

    idx = self._index_map[val]
    last_val = self._list[-1]

    # Swap target with last element
    self._list[idx] = last_val
    self._index_map[last_val] = idx

    # Remove last element
    self._list.pop()
    del self._index_map[val]

    return True
```

This is O(1) and fixes bug #4 (stale index entries) simultaneously — only the swapped element's index needs updating.

Note: edge case when `val` is the last element — the swap is a no-op, and it still works correctly because we update `_index_map[last_val] = idx` before deleting `_index_map[val]`, and when `val == last_val`, the delete removes the just-updated entry, which is correct.

### 2. `get_random` crashes on empty set

`random.choice([])` raises `IndexError`. Should handle gracefully.

Fix: check if empty first.

```python
def get_random(self) -> Optional[int]:
    if not self._list:
        return None
    return random.choice(self._list)
```

### 3. `insert` doesn't check for duplicates

Line 15 overwrites `_index_map[val]` and appends again — duplicates in the list, corrupted map.

Fix: check if already present.

```python
def insert(self, val: int) -> bool:
    if val in self._index_map:
        return False  # already present
    self._index_map[val] = len(self._list)
    self._list.append(val)
    return True
```

### 4. Stale index entries after removal

Already fixed by bug #1's swap-and-pop. The old code does `self._list.pop(idx)` which shifts all elements after `idx`, but never updates their entries in `_index_map`. With swap-and-pop, only the swapped element's index changes — one O(1) update.

The user's original idea of rebuilding the entire map (`{val: key for key, val in enumerate(list)}`) would work but is **O(n)** — defeats the purpose of the data structure.

---

## Feature Implementation Plan

### Feature 1: `get_random_weighted(weights)`

Each element has an associated weight. Use a parallel weights structure and weighted random selection.

```python
def __init__(self):
    self._list: list[int] = []
    self._index_map: dict[int, int] = {}
    self._weights: dict[int, float] = {}  # val -> weight, default 1.0

def set_weight(self, val: int, weight: float) -> bool:
    if val not in self._index_map:
        return False
    self._weights[val] = weight
    return True

def get_random_weighted(self) -> Optional[int]:
    if not self._list:
        return None
    weights = [self._weights.get(v, 1.0) for v in self._list]
    return random.choices(self._list, weights=weights, k=1)[0]
```

`random.choices` with weights handles the probability distribution. O(n) to build the weights list — could cache and invalidate on mutation for repeated calls.

### Feature 2: `bulk_insert(values)` and `bulk_remove(values)`

Batch operations, reuse single-element methods.

```python
def bulk_insert(self, values: list[int]) -> int:
    """Insert multiple values. Returns count of actually inserted."""
    count = 0
    for val in values:
        if self.insert(val):
            count += 1
    return count

def bulk_remove(self, values: list[int]) -> int:
    """Remove multiple values. Returns count of actually removed."""
    count = 0
    for val in values:
        if self.remove(val):
            count += 1
    return count
```

Each individual operation is O(1), so bulk is O(k) for k values.

### Feature 3: `get_random_n(n)`

Return n unique random elements. Like `random.sample`.

```python
def get_random_n(self, n: int) -> list[int]:
    if n <= 0:
        return []
    if n >= len(self._list):
        return list(self._list)  # return all, shuffled or not
    return random.sample(self._list, n)
```

`random.sample` returns unique elements without replacement. O(n).

### Feature 4: `__iter__`, `__len__`, `__contains__`

Pythonic dunder methods.

```python
def __iter__(self):
    return iter(self._list)

def __len__(self) -> int:
    return len(self._list)

def __contains__(self, val: int) -> bool:
    return val in self._index_map  # O(1) via hash map
```

### Feature 5: `snapshot()` and `restore(snapshot)`

Save and restore the full state. Deep copy to avoid aliasing.

```python
def snapshot(self) -> dict:
    return {
        "list": list(self._list),
        "index_map": dict(self._index_map),
        "weights": dict(self._weights),
    }

def restore(self, snap: dict) -> None:
    self._list = list(snap["list"])
    self._index_map = dict(snap["index_map"])
    self._weights = dict(snap["weights"])
```

Copy on both save and restore to prevent mutations from leaking between snapshots.

### Feature 6: Tests

- **Swap-and-pop**: insert [1,2,3], remove 1, verify list has no gaps, `_index_map` is consistent, `contains(1)` is False
- **Remove last element**: insert [1,2], remove 2 (edge case — swap with self), verify works
- **Empty get_random**: `get_random()` on empty set returns None
- **Duplicate insert**: insert 5 twice, second returns False, size stays 1
- **Stale index**: insert [1,2,3], remove 1, verify `_index_map[2]` and `_index_map[3]` point to correct indices
- **Weighted random**: insert values with weights 100:1, sample 1000 times, verify high-weight element selected ~99% of time
- **bulk_insert**: insert [1,2,3,2,4], returns 4 (one duplicate skipped), size is 4
- **bulk_remove**: remove [1,5,2], returns 2 (5 not found), size decremented by 2
- **get_random_n**: n=0 returns [], n > size returns all, n=3 returns 3 unique elements
- **Dunder methods**: `len(s)`, `5 in s`, `for x in s` all work correctly
- **Snapshot/restore**: insert values, snapshot, remove some, restore, verify original state is back
- **Snapshot isolation**: modify set after snapshot, verify snapshot is not affected
