VALID_STATUSES = ("online", "offline")


class ChargingStationTracker:
    """Per-station status history, queried by time window.

    DESIGN NOTES (things an interviewer will probe)

    Why a flat list of (timestamp, status) instead of merged intervals?
      A report is a state CHANGE, and the state holds until the next one, so
      consecutive reports already imply the intervals — storing explicit
      (start, end) pairs would mean rewriting the previous entry on every
      report. The list is append-only and stays sorted for free, which is the
      invariant every query below leans on.

    Why is the list sorted "for free"?
      The spec guarantees timestamps are monotonically increasing per station.
      That's load-bearing, not decorative — it's what makes binary search legal.
      report_status enforces it rather than trusting it, because a single
      out-of-order append silently corrupts every later query with no error.

    Complexity: report O(1), available O(log n) per station, uptime O(n).
    """

    def __init__(self) -> None:
        # station_id -> [(timestamp, status)], kept sorted by timestamp
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
        # Linear, not binary search: we need every online run overlapping the
        # window, not one lookup. Binary searching the first relevant report is
        # a real optimisation for long histories with short windows — say so,
        # but it doesn't change the O(n) worst case where the window spans all.
        for i in range(len(_slots)):
            slot_start, slot_status = _slots[i]
            if slot_status != "online":
                continue
            # An online report runs until the next report of ANY kind. The last
            # report has no successor, so it runs to `end` — that's what makes
            # a single ("online") report count as 100% uptime.
            slot_end = _slots[i + 1][0] if i + 1 < len(_slots) else end
            # Clip the run to the query window; the clamps handle runs that
            # start before `start` or finish after `end`.
            _slice = min(end, slot_end) - max(start, slot_start)
            # Negative means the run lies entirely outside the window. Guarding
            # here rather than skipping early keeps the two cases (before the
            # window, after it) in one branch.
            if _slice > 0:
                uptime += _slice
        # Fraction, not duration — end > start is guaranteed above, so this
        # can't divide by zero.
        return uptime/(end-start)

    def _latest_status(self, _slots: list[tuple[int, str]], timestamp: int) -> str | None:
        """Status of the most recent report at or before timestamp, None if there is none.

        Availability is decided by the LAST report at or before the query time,
        not by whether any report matches — with [(0, online), (10, offline)]
        a first-match scan would call the station online at t=20.

        This is the "rightmost value <= target" variant of binary search: when
        the midpoint qualifies, record it and keep going RIGHT looking for a
        later one, instead of returning immediately. `latest` holds the best
        candidate found so far, so the loop can run to exhaustion without
        needing a separate found/not-found flag.

        Returns None for a station that has never reported, which the caller
        treats as offline — that's the spec's "assume offline" default, and it
        falls out of the empty list making the loop body never run.
        """
        lo, hi = 0, len(_slots) - 1
        latest = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if _slots[mid][0] <= timestamp:
                latest = _slots[mid][1]
                lo = mid + 1  # qualifies, but a later one may too
            else:
                hi = mid - 1  # too late, discard this half
        return latest

    def get_available_stations(self, timestamp: int) -> list[str]:
        available_stations = []
        for station_id, _slots in self.stations.items():
            if self._latest_status(_slots, timestamp) == "online":
                available_stations.append(station_id)
        return available_stations

    def get_fleet_uptime(self, start: int, end: int) -> float:
        # Average of per-station fractions, so every station weighs the same
        # regardless of how many reports it filed. Empty fleet returns 0.0
        # rather than raising ZeroDivisionError — arbitrary, so flag it.
        if not self.stations:
            return 0.0
        total_uptime = 0
        for station_id in self.stations:
            total_uptime += self.get_uptime(station_id, start, end)
        return total_uptime/len(self.stations)
