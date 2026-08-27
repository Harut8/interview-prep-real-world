VALID_STATUSES = ("online", "offline")


class ChargingStationTracker:
    def __init__(self) -> None:
        self.stations: dict[str, list[tuple[int, str]]] = {}

    def _is_station_exist(self, station_id: str) -> bool:
        return station_id in self.stations

    def add_station(self, station_id: str) -> None:
        if not self._is_station_exist(station_id):
            self.stations[station_id] = []

    def report_status(self, station_id: str, timestamp: int, status: str) -> None:
        if not self._is_station_exist(station_id):
            raise ValueError("Station does not exist")
        if status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {VALID_STATUSES}, got {status!r}")
        _slots = self.stations[station_id]
        # The interval maths and the binary search in _latest_status both assume
        # reports arrive in timestamp order, so reject anything that breaks it.
        if _slots and timestamp < _slots[-1][0]:
            raise ValueError("Timestamps must be non-decreasing per station")
        _slots.append((timestamp, status))

    def get_uptime(self, station_id: str, start: int, end: int) -> float:
        """Fraction of [start, end) the station was online, in 0.0-1.0.

        Each report holds until the next one; the final report holds until `end`.

            A: [(10, "online"), (20, "offline")]
            get_uptime("A", 18, 25) -> 2 / 7

            10-------20-----
            -------18----------25
        """
        if not self._is_station_exist(station_id):
            raise ValueError("Station does not exist")
        if end <= start:
            raise ValueError("End time must be greater than start time")
        _slots = self.stations[station_id]
        uptime = 0
        for i in range(len(_slots)):
            slot_start, slot_status = _slots[i]
            if slot_status != "online":
                continue
            slot_end = _slots[i + 1][0] if i + 1 < len(_slots) else end
            _slice = min(end, slot_end) - max(start, slot_start)
            if _slice > 0:
                uptime += _slice
        return uptime/(end-start)

    def _latest_status(self, _slots: list[tuple[int, str]], timestamp: int) -> str | None:
        """Status of the most recent report at or before timestamp, None if there is none."""
        lo, hi = 0, len(_slots) - 1
        latest = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if _slots[mid][0] <= timestamp:
                latest = _slots[mid][1]
                lo = mid + 1
            else:
                hi = mid - 1
        return latest

    def get_available_stations(self, timestamp: int) -> list[str]:
        available_stations = []
        for station_id, _slots in self.stations.items():
            if self._latest_status(_slots, timestamp) == "online":
                available_stations.append(station_id)
        return available_stations

    def get_fleet_uptime(self, start: int, end: int) -> float:
        if not self.stations:
            return 0.0
        total_uptime = 0
        for station_id in self.stations:
            total_uptime += self.get_uptime(station_id, start, end)
        return total_uptime/len(self.stations)
