# My Solution — Task 23

## Bug Fixes

### 1. `hit` silently ignores out-of-order timestamps

Line 25-26 rejects any hit with a timestamp older than the latest:
```python
if self._hits and timestamp < self._hits[-1].timestamp:
    return
```
Late-arriving hits are simply dropped. In a real system, network delays mean hits can arrive out of order.

Fix: remove the early return, use `bisect.insort` to insert in sorted position so the list stays sorted.

```python
import bisect

def hit(self, timestamp: float, source: str = "unknown") -> None:
    record = HitRecord(timestamp=timestamp, source=source)
    # Insert in sorted order — handles out-of-order timestamps
    bisect.insort(self._hits, record)  # requires __lt__ on HitRecord
    self._source_counts[source] += 1
```

Need to add `__lt__` to HitRecord:
```python
@dataclass
class HitRecord:
    timestamp: float
    source: str = "unknown"

    def __lt__(self, other):
        return self.timestamp < other.timestamp
```

### 2. `get_hits` scans ALL hits — O(n) cleanup

`_cleanup` uses a list comprehension over every hit. Since the list is sorted (after fix #1), we can use `bisect.bisect_left` to find the cutoff index and slice — O(log n) search + O(k) removal for k expired hits.

Fix:
```python
def _cleanup(self, current_timestamp: float) -> None:
    cutoff = current_timestamp - self._window_size
    # Find first index where timestamp >= cutoff
    idx = bisect.bisect_left(self._hits, HitRecord(timestamp=cutoff))
    # Remove everything before that index
    removed = self._hits[:idx]
    self._hits = self._hits[idx:]
    # Update source counts for removed hits
    for h in removed:
        self._source_counts[h.source] -= 1
        if self._source_counts[h.source] <= 0:
            del self._source_counts[h.source]
```

Note: `_source_counts` must also be decremented when hits are cleaned up — the original code never does this, so source counts grow forever.

### 3. `_cleanup` off-by-one — removes hits at exactly the boundary

Line 43: `h.timestamp > cutoff` excludes hits at exactly `current - 300`. A hit exactly 300 seconds ago should still count.

Fix: change `>` to `>=`.

```python
cutoff = current_timestamp - self._window_size
# With bisect approach: use bisect_left with cutoff timestamp
# bisect_left finds first element >= cutoff, so elements at exactly cutoff are kept ✓
```

If staying with the list comprehension approach:
```python
self._hits = [h for h in self._hits if h.timestamp >= cutoff]
```

### 4. Thread safety — concurrent `hit()` calls cause data races

No locking anywhere. Multiple threads calling `hit()` simultaneously can corrupt `_hits` list and `_source_counts` dict.

Fix: use `threading.Lock` to protect all mutations and reads.

```python
import threading

class HitCounter:
    def __init__(self, window_size: int = 300):
        self._hits: list[HitRecord] = []
        self._source_counts: dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
        self._window_size = window_size

    def hit(self, timestamp: float, source: str = "unknown") -> None:
        record = HitRecord(timestamp=timestamp, source=source)
        with self._lock:
            bisect.insort(self._hits, record)
            self._source_counts[source] += 1

    def get_hits(self, timestamp: float) -> int:
        with self._lock:
            self._cleanup(timestamp)
            return len(self._hits)
```

All public methods (`hit`, `get_hits`, `get_total_hits`, `reset`) need `with self._lock`. `_cleanup` is called inside the lock so it doesn't need its own.

---

## Feature Implementation Plan

### Feature 1: Configurable window size

Make `WINDOW_SIZE` an instance parameter instead of a global constant.

```python
class HitCounter:
    def __init__(self, window_size: int = 300):
        self._window_size = window_size
        # ... rest of init
```

Replace all references to `WINDOW_SIZE` with `self._window_size`.

### Feature 2: `get_hits_per_second(timestamp)`

Returns the hit rate (hits/sec) over the current window.

```python
def get_hits_per_second(self, timestamp: float) -> float:
    with self._lock:
        self._cleanup(timestamp)
        count = len(self._hits)
        if count == 0:
            return 0.0
        # Window spans from earliest hit to timestamp, or full window
        earliest = self._hits[0].timestamp
        actual_window = min(timestamp - earliest, self._window_size)
        if actual_window <= 0:
            return float(count)
        return count / actual_window
```

### Feature 3: `get_hit_breakdown(timestamp, bucket_size)`

Splits the window into buckets and counts hits per bucket. Returns `{bucket_start: count}`.

```python
def get_hit_breakdown(self, timestamp: float, bucket_size: int = 60) -> dict[float, int]:
    with self._lock:
        self._cleanup(timestamp)
        window_start = timestamp - self._window_size
        breakdown = {}

        # Initialize buckets
        bucket_start = window_start
        while bucket_start < timestamp:
            breakdown[bucket_start] = 0
            bucket_start += bucket_size

        # Count hits into buckets
        for h in self._hits:
            # Which bucket does this hit belong to?
            bucket = window_start + ((h.timestamp - window_start) // bucket_size) * bucket_size
            if bucket in breakdown:
                breakdown[bucket] += 1

        return breakdown
```

### Feature 4: `merge(other_counter)`

Combine hits from another HitCounter instance. Used for distributed aggregation (e.g., merging counters from multiple servers).

```python
def merge(self, other: "HitCounter") -> None:
    with self._lock:
        with other._lock:
            for hit_record in other._hits:
                bisect.insort(self._hits, hit_record)
                self._source_counts[hit_record.source] += 1
```

Note: need consistent lock ordering to avoid deadlocks if two counters merge each other concurrently. Use `id()` to order: always lock the one with smaller `id()` first.

```python
def merge(self, other: "HitCounter") -> None:
    # Consistent lock ordering to prevent deadlock
    first, second = (self, other) if id(self) < id(other) else (other, self)
    with first._lock:
        with second._lock:
            for hit_record in other._hits:
                bisect.insort(self._hits, hit_record)
                self._source_counts[hit_record.source] += 1
```

### Feature 5: `top_sources(timestamp, n)`

Returns the top N sources by hit count within the current window.

```python
def top_sources(self, timestamp: float, n: int = 5) -> list[tuple[str, int]]:
    with self._lock:
        self._cleanup(timestamp)
        # _source_counts is maintained during cleanup, so it's accurate
        sorted_sources = sorted(
            self._source_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_sources[:n]
```

### Feature 6: Tests

- **Out-of-order hits**: add hits at t=10, t=5, t=15 — all three are counted, order is correct
- **Efficient window (bisect)**: add 1000 hits, verify `get_hits` returns correct count (functional correctness)
- **Off-by-one**: add hit at t=100, call `get_hits(400)` — hit at exactly 300 seconds ago should still count. Call `get_hits(401)` — now it's gone
- **Thread safety**: spawn 100 threads each calling `hit()` simultaneously, verify total count is exactly 100
- **Configurable window**: create counter with `window_size=10`, verify hits expire after 10 seconds not 300
- **get_hits_per_second**: add 10 hits over 5 seconds, verify rate is 2.0
- **get_hit_breakdown**: add hits across a range, verify bucket counts sum to total, verify correct bucket assignment
- **merge**: create two counters with different hits, merge, verify combined count and source counts
- **merge deadlock**: merge A into B and B into A concurrently — should not deadlock
- **top_sources**: add hits from sources "a"(10x), "b"(5x), "c"(3x), verify `top_sources(t, 2)` returns [("a", 10), ("b", 5)]
- **cleanup updates source_counts**: add hits, wait for expiry, verify source_counts are decremented