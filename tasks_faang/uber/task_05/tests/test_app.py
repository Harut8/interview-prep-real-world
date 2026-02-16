"""
Tests for Driver Location Tracker.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import time
from app import (
    encode_geohash,
    LocationUpdate,
    DriverLocation,
    driver_locations,
    geohash_index,
    update_driver_location,
    get_nearby_drivers,
    get_driver_latest_location,
    get_driver_history,
    GEOHASH_PRECISION,
    STALE_TIMEOUT_SECONDS,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all state before each test."""
    driver_locations.clear()
    geohash_index.clear()
    yield
    driver_locations.clear()
    geohash_index.clear()


class TestGeohash:
    def test_same_location_same_hash(self):
        """This test should PASS — identical coords produce same hash."""
        h1 = encode_geohash(37.7749, -122.4194)
        h2 = encode_geohash(37.7749, -122.4194)
        assert h1 == h2

    def test_nearby_locations_share_prefix(self):
        """This test should PASS — nearby points share geohash prefix."""
        h1 = encode_geohash(37.7749, -122.4194)
        h2 = encode_geohash(37.7750, -122.4195)
        # At least first 3 characters should match for very close points
        assert h1[:3] == h2[:3]

    def test_geohash_precision_sufficient(self):
        """
        FAILING: Geohash precision is 4, which is ~40km cell.
        For ride matching, we need precision 6+ (~1km cell).
        Two points 2km apart may fall in different cells at precision 6+
        but always in the same cell at precision 4.
        """
        # These two points are ~2km apart
        h1 = encode_geohash(37.7749, -122.4194)  # SF downtown
        h2 = encode_geohash(37.7900, -122.4194)  # ~1.7km north

        # With precision 6+, these should be in different cells
        # With precision 4, they're in the same cell (too coarse)
        assert GEOHASH_PRECISION >= 6, (
            f"Geohash precision {GEOHASH_PRECISION} is too low; need >= 6"
        )


class TestLocationUpdates:
    def test_update_stores_location(self):
        """This test should PASS — update creates a location record."""
        update = update_driver_location("d1", 37.7749, -122.4194, time.time())
        assert update.driver_id == "d1"

        loc = get_driver_latest_location("d1")
        assert loc is not None
        assert loc.latitude == pytest.approx(37.7749)

    def test_history_ordered_by_timestamp(self):
        """
        FAILING: History should be ordered by timestamp, not insertion order.
        Late-arriving updates break the ordering.
        """
        now = time.time()
        # Insert out of order (e.g., GPS update arrived late)
        update_driver_location("d1", 37.77, -122.41, now - 10)  # 10s ago
        update_driver_location("d1", 37.78, -122.42, now - 30)  # 30s ago (late)
        update_driver_location("d1", 37.79, -122.43, now - 20)  # 20s ago (late)

        history = get_driver_history("d1")
        timestamps = [h.timestamp for h in history]
        assert timestamps == sorted(timestamps), (
            "History is not sorted by timestamp"
        )

    def test_latest_is_most_recent_by_timestamp(self):
        """
        FAILING: Latest should be the update with the most recent timestamp,
        not the most recently inserted.
        """
        now = time.time()
        update_driver_location("d1", 37.77, -122.41, now)       # newest
        update_driver_location("d1", 37.78, -122.42, now - 60)  # older (late arrival)

        latest = get_driver_latest_location("d1")
        assert latest is not None
        assert latest.timestamp == pytest.approx(now, abs=1.0), (
            "Latest location should be the one with the most recent timestamp"
        )


class TestNearbyDrivers:
    def test_finds_driver_in_same_cell(self):
        """This test should PASS — driver in same geohash cell is returned."""
        update_driver_location("d1", 37.7749, -122.4194, time.time())
        nearby = get_nearby_drivers(37.7750, -122.4195)
        driver_ids = [d.driver_id for d in nearby]
        assert "d1" in driver_ids

    def test_stale_drivers_excluded(self):
        """
        FAILING: Drivers with locations older than STALE_TIMEOUT_SECONDS
        should not be returned. Currently no staleness check.
        """
        stale_time = time.time() - STALE_TIMEOUT_SECONDS - 60  # 6 min old
        update_driver_location("d_stale", 37.7749, -122.4194, stale_time)

        fresh_time = time.time()
        update_driver_location("d_fresh", 37.7750, -122.4195, fresh_time)

        nearby = get_nearby_drivers(37.7749, -122.4194)
        driver_ids = [d.driver_id for d in nearby]
        assert "d_stale" not in driver_ids, "Stale driver should be excluded"
        assert "d_fresh" in driver_ids


class TestGeofencing:
    # TODO: Implement geofencing alerts
    # def test_driver_enters_zone_triggers_alert(self):
    #     """When a driver enters a defined zone, an alert should be emitted."""
    #     pass

    # TODO: Driver exits zone
    # def test_driver_exits_zone_triggers_alert(self):
    #     """When a driver leaves a zone they were in, an exit alert fires."""
    #     pass
    pass


class TestLocationHistory:
    # TODO: Implement location history trail query
    # def test_get_trail_for_time_period(self):
    #     """Should return ordered (lat, lon, ts) points for a time range."""
    #     pass

    # TODO: Trail distance calculation
    # def test_trail_total_distance(self):
    #     """Calculate total distance traveled from the trail."""
    #     pass
    pass
