# Carbon Savings Calculator (Time-Weighted Intervals)

**Energy-domain flavor — maps to LC 370 Range Addition / LC 1094 Car Pooling.**

Implement a system that tracks carbon offset events over time intervals and answers aggregate queries.

## Interface

```python
class CarbonTracker:
    def __init__(self) -> None: ...
    def add_offset(self, start: int, end: int, kg_co2_per_hour: float) -> None: ...
    def total_savings(self, start: int, end: int) -> float: ...
    def peak_offset_rate(self, start: int, end: int) -> float: ...
    def snapshot(self, timestamp: int) -> float: ...
```

## Requirements

- `add_offset(start, end, rate)` — registers a carbon offset of `rate` kg CO2/hour active during `[start, end)`.
- Multiple overlapping offsets stack additively.
- `total_savings(start, end)` — returns total kg CO2 saved in `[start, end)`.
- `peak_offset_rate(start, end)` — returns the maximum instantaneous offset rate (sum of overlapping rates) in the window.
- `snapshot(timestamp)` — returns the current offset rate at a point in time.

## Patterns Tested

Difference arrays / sweep line, interval overlap, prefix sums.

## What You Should Do

1. Write tests first.
2. Consider: brute-force first, then optimize with a sweep-line / difference array.

## Time Target: 45 minutes
