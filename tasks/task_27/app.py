from dataclasses import dataclass


@dataclass
class Interval:
    start: float
    end: float

    def __repr__(self):
        return f"[{self.start}, {self.end}]"

    def length(self) -> float:
        return max(0, self.end - self.start)


class IntervalManager:
    """Manages operations on sorted lists of non-overlapping intervals."""

    def find_intersections(
        self, list_a: list[Interval], list_b: list[Interval]
    ) -> list[Interval]:
        """Find all intersections between two sorted interval lists."""
        result = []
        i, j = 0, 0

        while i < len(list_a) and j < len(list_b):
            a = list_a[i]
            b = list_b[j]

            # BUG: fails when one interval completely contains another
            # Only detects partial overlaps where a.start < b.start
            if a.start < b.start and a.end > b.start and a.end < b.end:
                result.append(Interval(b.start, a.end))
                i += 1
            elif b.start < a.start and b.end > a.start and b.end < a.end:
                result.append(Interval(a.start, b.end))
                j += 1
            else:
                if a.end <= b.start:
                    i += 1
                else:
                    j += 1

        return result

    def merge_intervals(self, intervals: list[Interval]) -> list[Interval]:
        """Merge overlapping intervals."""
        if not intervals:
            return []

        sorted_intervals = sorted(intervals, key=lambda iv: iv.start)
        merged = [Interval(sorted_intervals[0].start, sorted_intervals[0].end)]

        for current in sorted_intervals[1:]:
            last = merged[-1]
            # BUG: uses >= instead of > — doesn't merge adjacent intervals
            # [1,3] and [3,5] should merge to [1,5] but >= treats them as separate
            if current.start >= last.end:
                merged.append(Interval(current.start, current.end))
            else:
                last.end = max(last.end, current.end)

        return merged

    def insert_interval(
        self, intervals: list[Interval], new_interval: Interval
    ) -> list[Interval]:
        """Insert a new interval and merge if needed."""
        # BUG: just appends without maintaining sorted order
        intervals.append(new_interval)
        return self.merge_intervals(intervals)

    def is_point_in_any(self, intervals: list[Interval], point: float) -> bool:
        """Check if a point falls within any interval."""
        # BUG: linear scan instead of binary search on sorted intervals
        for interval in intervals:
            if interval.start <= point <= interval.end:
                return True
        return False

    def total_coverage(self, intervals: list[Interval]) -> float:
        """Calculate total covered length (after merging overlaps)."""
        merged = self.merge_intervals(intervals)
        return sum(iv.length() for iv in merged)


# TODO: Add subtract(intervals, to_remove) method
# TODO: Add union(list_a, list_b) method
# TODO: Add gaps(intervals) method
# TODO: Add IntervalTree class for efficient queries
