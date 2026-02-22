import time
from dataclasses import dataclass, field
from collections import defaultdict


WINDOW_SIZE = 300  # 5 minutes in seconds


@dataclass
class HitRecord:
    timestamp: float
    source: str = "unknown"


class HitCounter:
    """Counts hits within a sliding time window."""

    def __init__(self):
        self._hits: list[HitRecord] = []
        self._source_counts: dict[str, int] = defaultdict(int)

    def hit(self, timestamp: float, source: str = "unknown") -> None:
        """Record a hit at the given timestamp."""
        # BUG: silently ignores hits with timestamps older than the latest
        if self._hits and timestamp < self._hits[-1].timestamp:
            return

        record = HitRecord(timestamp=timestamp, source=source)
        self._hits.append(record)
        self._source_counts[source] += 1

    def get_hits(self, timestamp: float) -> int:
        """Return number of hits in the past WINDOW_SIZE seconds."""
        # BUG: scans ALL hits — O(n) instead of using efficient window
        self._cleanup(timestamp)
        return len(self._hits)

    def _cleanup(self, current_timestamp: float) -> None:
        """Remove hits outside the time window."""
        # BUG: off-by-one — removes hits at exactly the boundary
        # A hit at (current - 300) should still be counted
        cutoff = current_timestamp - WINDOW_SIZE
        self._hits = [h for h in self._hits if h.timestamp > cutoff]

    def get_total_hits(self) -> int:
        """Return total number of hits ever recorded."""
        return len(self._hits)

    def reset(self) -> None:
        """Clear all recorded hits."""
        self._hits.clear()
        self._source_counts.clear()


# TODO: Add configurable window size
# TODO: Add get_hits_per_second(timestamp) method
# TODO: Add get_hit_breakdown(timestamp, bucket_size) method
# TODO: Add merge(other_counter) method
# TODO: Add top_sources(timestamp, n) method
# TODO: Add thread safety
