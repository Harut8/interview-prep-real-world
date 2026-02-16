"""
Tests for Ride Matching Service.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import threading
import time
from app import (
    haversine_distance,
    Location,
    Driver,
    DriverStatus,
    find_nearest_driver,
    match_rider_with_driver,
    drivers,
    match_history,
    estimate_eta,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all in-memory state before each test."""
    drivers.clear()
    match_history.clear()
    yield
    drivers.clear()
    match_history.clear()


def _add_driver(driver_id: str, lat: float, lon: float,
                status: DriverStatus = DriverStatus.AVAILABLE,
                rating: float = 5.0) -> Driver:
    driver = Driver(
        driver_id=driver_id,
        name=f"Driver {driver_id}",
        location=Location(latitude=lat, longitude=lon),
        status=status,
        rating=rating,
    )
    drivers[driver_id] = driver
    return driver


class TestHaversineDistance:
    def test_same_location_returns_zero(self):
        """This test should PASS — same point should give 0 distance."""
        loc = Location(latitude=37.7749, longitude=-122.4194)
        dist = haversine_distance(loc, loc)
        assert dist == pytest.approx(0.0, abs=0.01)

    def test_known_distance_sf_to_la(self):
        """
        FAILING: Distance from SF to LA should be ~559 km.
        The haversine bug causes incorrect distance calculation.
        """
        sf = Location(latitude=37.7749, longitude=-122.4194)
        la = Location(latitude=34.0522, longitude=-118.2437)
        dist = haversine_distance(sf, la)
        # Known distance SF to LA is approximately 559 km
        assert dist == pytest.approx(559.0, rel=0.05)

    def test_distance_is_symmetric(self):
        """
        FAILING: Distance A->B should equal B->A.
        Bug in haversine makes this non-symmetric due to addition.
        """
        loc1 = Location(latitude=40.7128, longitude=-74.0060)  # NYC
        loc2 = Location(latitude=51.5074, longitude=-0.1278)   # London
        d1 = haversine_distance(loc1, loc2)
        d2 = haversine_distance(loc2, loc1)
        assert d1 == pytest.approx(d2, rel=0.001)


class TestFindNearestDriver:
    def test_finds_closest_driver(self):
        """
        FAILING: Should find the closest driver, but haversine bug
        may cause wrong driver to be selected.
        """
        _add_driver("d1", 37.78, -122.42)  # ~0.5 km away
        _add_driver("d2", 37.80, -122.45)  # ~3 km away
        _add_driver("d3", 38.00, -122.50)  # ~25 km away

        rider_loc = Location(latitude=37.7749, longitude=-122.4194)
        driver = find_nearest_driver(rider_loc)

        assert driver is not None
        assert driver.driver_id == "d1"

    def test_skips_busy_drivers(self):
        """This test should PASS — busy drivers should be skipped."""
        _add_driver("d1", 37.78, -122.42, status=DriverStatus.BUSY)
        _add_driver("d2", 37.80, -122.45, status=DriverStatus.AVAILABLE)

        rider_loc = Location(latitude=37.7749, longitude=-122.4194)
        driver = find_nearest_driver(rider_loc)

        assert driver is not None
        assert driver.driver_id == "d2"

    def test_race_condition_concurrent_matches(self):
        """
        FAILING: Two concurrent match requests can grab the same driver
        because status update is not atomic.
        """
        _add_driver("d_only", 37.78, -122.42)

        results = []

        def do_match():
            rider_loc = Location(latitude=37.7749, longitude=-122.4194)
            d = find_nearest_driver(rider_loc)
            results.append(d)

        t1 = threading.Thread(target=do_match)
        t2 = threading.Thread(target=do_match)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # At most one should get the driver; the other should get None
        matched_drivers = [r for r in results if r is not None]
        assert len(matched_drivers) <= 1, (
            "Race condition: same driver matched to multiple riders"
        )


class TestMatchTimeout:
    def test_match_returns_none_when_no_drivers(self):
        """This test should PASS (returns None), but there's no timeout logic."""
        result = match_rider_with_driver("r1", 37.77, -122.41)
        assert result is None

    # TODO: Implement match request timeout
    # def test_match_timeout_raises_after_deadline(self):
    #     """Match request should raise or return a timeout error after N seconds."""
    #     pass

    # TODO: Implement match retry with timeout
    # def test_match_retries_until_timeout(self):
    #     """Match should retry finding a driver until timeout expires."""
    #     pass


class TestMatchScoring:
    # TODO: Implement composite match scoring with ETA and rating
    # def test_score_weighs_distance_and_rating(self):
    #     """A closer driver with lower rating might lose to slightly
    #     farther driver with much higher rating."""
    #     pass

    # TODO: Score breakdown in match result
    # def test_match_result_includes_score_breakdown(self):
    #     """Match result should include distance_score, rating_score, total_score."""
    #     pass
    pass


class TestSurgeZoneAwareness:
    # TODO: Implement surge zone awareness
    # def test_match_in_surge_zone_prefers_drivers_in_zone(self):
    #     """When rider is in a surge zone, only drivers in/near the zone
    #     should be considered for matching."""
    #     pass

    # TODO: Surge zone radius buffer
    # def test_surge_zone_buffer_radius(self):
    #     """Drivers just outside the surge zone but within buffer
    #     should still be eligible."""
    #     pass
    pass
