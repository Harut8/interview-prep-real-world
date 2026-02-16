"""
Tests for Fleet Analytics Dashboard API.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from app import (
    TripRecord,
    DriverSnapshot,
    DriverStatus,
    DailyMetric,
    trip_records,
    driver_snapshots,
    daily_metrics,
    calculate_moving_average,
    detect_peak_hours,
    calculate_utilization,
    get_daily_trip_counts,
    CITY_TIMEZONE_OFFSETS,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all state before each test."""
    trip_records.clear()
    driver_snapshots.clear()
    daily_metrics.clear()
    yield
    trip_records.clear()
    driver_snapshots.clear()
    daily_metrics.clear()


def _make_trip(trip_id: str, zone: str = "sf", started_at: float = None,
               completed_at: float = None, fare_cents: int = 2000,
               wait_seconds: float = 180, duration_min: float = 15.0) -> TripRecord:
    now = time.time()
    if started_at is None:
        started_at = now - 900  # 15 min ago
    if completed_at is None:
        completed_at = now
    trip = TripRecord(
        trip_id=trip_id, driver_id=f"d_{trip_id}", zone=zone,
        started_at=started_at, completed_at=completed_at,
        fare_cents=fare_cents, wait_time_seconds=wait_seconds,
        duration_minutes=duration_min,
    )
    trip_records.append(trip)
    return trip


def _add_driver(driver_id: str, status: DriverStatus, zone: str = "sf"):
    driver_snapshots[driver_id] = DriverSnapshot(
        driver_id=driver_id, status=status, zone=zone,
    )


class TestMovingAverage:
    def test_simple_moving_average(self):
        """
        FAILING: 7-day moving average should use exactly 7 values.
        Bug: window is off by one, only uses 6 values.
        """
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        result = calculate_moving_average(values, window=7)

        # First moving average: avg(10,20,30,40,50,60,70) = 280/7 = 40.0
        assert result[0] == pytest.approx(40.0), (
            f"Expected 40.0 but got {result[0]} — window size is wrong"
        )

    def test_window_equals_list_length(self):
        """This test should PASS — window equals data length."""
        values = [10, 20, 30]
        result = calculate_moving_average(values, window=3)
        assert result[0] == pytest.approx(20.0)

    def test_empty_values(self):
        """This test should PASS — empty input returns empty."""
        result = calculate_moving_average([], window=7)
        assert result == []


class TestPeakHours:
    def test_peak_hours_timezone_conversion(self):
        """
        FAILING: Peak hours should be reported in local time.
        For SF (UTC-8), a trip at 10 PM UTC should show as 2 PM local.
        """
        # Create a trip at 22:00 UTC (2 PM Pacific)
        utc_dt = datetime(2024, 6, 15, 22, 0, 0, tzinfo=timezone.utc)
        started_at = utc_dt.timestamp()

        _make_trip("t1", started_at=started_at,
                   completed_at=started_at + 900)

        peaks = detect_peak_hours(trip_records, city="san_francisco")
        assert len(peaks) > 0

        # Peak hour should be 14 (2 PM local), not 22 (10 PM UTC)
        peak_hour = peaks[0]["hour"]
        expected_local = 22 + CITY_TIMEZONE_OFFSETS["san_francisco"]  # 22 + (-8) = 14
        assert peak_hour == expected_local, (
            f"Peak hour {peak_hour} is UTC, should be {expected_local} local"
        )


class TestUtilization:
    def test_normal_utilization(self):
        """This test should PASS — basic utilization calculation."""
        _add_driver("d1", DriverStatus.ONLINE_AVAILABLE)
        _add_driver("d2", DriverStatus.ONLINE_BUSY)
        _add_driver("d3", DriverStatus.ONLINE_AVAILABLE)
        _add_driver("d4", DriverStatus.ONLINE_BUSY)

        result = calculate_utilization()
        # 2 busy / 4 online = 50%
        assert result["utilization_pct"] == pytest.approx(50.0)

    def test_utilization_does_not_exceed_100(self):
        """
        FAILING: Utilization should never exceed 100%.
        When a driver goes offline but their snapshot still says BUSY,
        busy_count can exceed online_count.
        """
        # 2 online drivers
        _add_driver("d1", DriverStatus.ONLINE_AVAILABLE)
        _add_driver("d2", DriverStatus.ONLINE_BUSY)
        # 2 offline drivers still marked "busy" in stale snapshots
        _add_driver("d3", DriverStatus.OFFLINE)
        _add_driver("d4", DriverStatus.OFFLINE)

        # Simulate stale data: d3 and d4 have old "busy" snapshots
        # but later went offline (status updated to OFFLINE)
        # The bug is that the busy_count check looks at ALL drivers
        # with ONLINE_BUSY status.
        # To trigger the bug, let's directly set them to ONLINE_BUSY
        # then only count d1+d2 as online total
        driver_snapshots["d3"].status = DriverStatus.ONLINE_BUSY
        driver_snapshots["d4"].status = DriverStatus.ONLINE_BUSY

        # Now we have 3 ONLINE_BUSY and 1 ONLINE_AVAILABLE = 4 online, 3 busy
        # But conceptually d3 & d4 should be OFFLINE
        # The real issue: busy_count includes ALL with ONLINE_BUSY status
        result = calculate_utilization()
        assert result["utilization_pct"] <= 100.0, (
            f"Utilization {result['utilization_pct']}% exceeds 100%"
        )


class TestPercentiles:
    # TODO: Implement percentile calculations
    # def test_p50_trip_duration(self):
    #     """P50 of [10, 20, 30, 40, 50] should be 30."""
    #     pass

    # TODO: P95 calculation
    # def test_p95_fare(self):
    #     """P95 should return the value at the 95th percentile rank."""
    #     pass

    # TODO: P99 with small dataset
    # def test_p99_small_dataset(self):
    #     """P99 with < 100 data points should still work."""
    #     pass
    pass


class TestWeekOverWeek:
    # TODO: Implement comparative analytics
    # def test_wow_trip_count_change(self):
    #     """Should show this week vs last week trip count diff."""
    #     pass

    # TODO: Percentage change calculation
    # def test_wow_percentage_change(self):
    #     """Should calculate correct percentage change."""
    #     pass
    pass


class TestCSVExport:
    # TODO: Implement CSV export endpoint
    # def test_csv_export_daily_metrics(self):
    #     """Should return valid CSV with daily metric rows."""
    #     pass

    # TODO: CSV headers
    # def test_csv_has_correct_headers(self):
    #     """CSV should have date, trips, fare, duration, wait headers."""
    #     pass
    pass
