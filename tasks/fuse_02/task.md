# EV Charging Station Uptime Tracker

**Energy-domain flavor — maps to LC 253 Meeting Rooms II / LC 1244 Design a Leaderboard.**

Implement a system that tracks EV charging station uptime/downtime and answers queries about availability in time windows.

## Interface

```python
class ChargingStationTracker:
    def __init__(self) -> None: ...
    def add_station(self, station_id: str) -> None: ...
    def report_status(self, station_id: str, timestamp: int, status: str) -> None: ...
    def get_uptime(self, station_id: str, start: int, end: int) -> float: ...
    def get_available_stations(self, timestamp: int) -> list[str]: ...
    def get_fleet_uptime(self, start: int, end: int) -> float: ...
```

## Requirements

- `report_status(station_id, timestamp, status)` — status is `"online"` or `"offline"`. Timestamps are monotonically increasing per station.
- `get_uptime(station_id, start, end)` — returns the fraction (0.0–1.0) of time the station was online in `[start, end]`.
- `get_available_stations(timestamp)` — returns all station IDs that are online at the given time.
- `get_fleet_uptime(start, end)` — returns average uptime across all stations.
- Handle stations with no status reports (assume offline).

## Patterns Tested

Interval merging, time-weighted calculations, sorted containers / binary search.

## What You Should Do

1. Write tests first.
2. Implement incrementally.

## Time Target: 45 minutes
