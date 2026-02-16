"""
Tests for Trip Fare Calculator.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
from app import (
    Trip,
    TripStatus,
    FareResult,
    calculate_fare,
    trips,
    fare_results,
    BASE_FARE,
    PER_KM_RATE,
    PER_MINUTE_RATE,
    MINIMUM_FARE,
    BOOKING_FEE,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all in-memory state before each test."""
    trips.clear()
    fare_results.clear()
    yield
    trips.clear()
    fare_results.clear()


def _make_trip(trip_id: str = "t1", distance_km: float = 10.0,
               duration_min: float = 20.0, surge: float = 1.0,
               tip: float = 0.0, tolls: float = 0.0) -> Trip:
    return Trip(
        trip_id=trip_id,
        rider_id="r1",
        driver_id="d1",
        distance_km=distance_km,
        duration_minutes=duration_min,
        surge_multiplier=surge,
        tip_amount=tip,
        toll_amount=tolls,
    )


class TestBasicFare:
    def test_standard_trip_no_surge(self):
        """This test should PASS — basic fare calculation without surge."""
        trip = _make_trip(distance_km=10.0, duration_min=20.0)
        fare = calculate_fare(trip)

        expected_base = BASE_FARE  # 2.50
        expected_distance = 10.0 * PER_KM_RATE  # 15.00
        expected_time = 20.0 * PER_MINUTE_RATE  # 5.00
        expected_total = expected_base + expected_distance + expected_time + BOOKING_FEE
        # 2.50 + 15.00 + 5.00 + 1.75 = 24.25

        assert fare.total == pytest.approx(expected_total, abs=0.01)

    def test_trip_with_surge(self):
        """This test should PASS — surge applied to base+distance+time."""
        trip = _make_trip(distance_km=10.0, duration_min=20.0, surge=2.0)
        fare = calculate_fare(trip)

        # (2.50 + 15.00 + 5.00) * 2.0 + 1.75 = 46.75
        metered = BASE_FARE + 10.0 * PER_KM_RATE + 20.0 * PER_MINUTE_RATE
        expected_total = metered * 2.0 + BOOKING_FEE
        assert fare.total == pytest.approx(expected_total, abs=0.01)


class TestTipBug:
    def test_tip_not_surged(self):
        """
        FAILING: Tip should NOT be multiplied by surge.
        Currently tip is added before surge, so a $5 tip with 2x surge
        becomes $10 tip.
        """
        trip = _make_trip(distance_km=10.0, duration_min=20.0,
                         surge=2.0, tip=5.0)
        fare = calculate_fare(trip)

        # Correct: (2.50 + 15.00 + 5.00) * 2.0 + 5.00 tip + 1.75 = 51.75
        metered = BASE_FARE + 10.0 * PER_KM_RATE + 20.0 * PER_MINUTE_RATE
        expected = metered * 2.0 + 5.0 + BOOKING_FEE
        assert fare.total == pytest.approx(expected, abs=0.01), (
            f"Tip is being surged! Got {fare.total}, expected {expected}"
        )


class TestFloatingPoint:
    def test_fare_rounds_to_cents(self):
        """
        FAILING: Fare should be rounded to 2 decimal places.
        With certain inputs, floating point produces values like 10.004999...
        """
        # 3.3 km * 1.50 = 4.95, 7.7 min * 0.25 = 1.925
        # base=2.50, total metered=9.375, + booking=11.125 -> should be 11.13 or 11.12
        trip = _make_trip(distance_km=3.3, duration_min=7.7)
        fare = calculate_fare(trip)

        # Total should be a clean 2-decimal value
        assert fare.total == round(fare.total, 2), (
            f"Fare {fare.total} has more than 2 decimal places"
        )


class TestMinimumFare:
    def test_very_short_trip_meets_minimum(self):
        """
        FAILING: Very short trips should still charge MINIMUM_FARE ($5.00).
        A 0.1 km, 1 min trip: 2.50 + 0.15 + 0.25 + 1.75 = 4.65 (below $5 min).
        """
        trip = _make_trip(distance_km=0.1, duration_min=1.0)
        fare = calculate_fare(trip)

        assert fare.total >= MINIMUM_FARE, (
            f"Fare {fare.total} is below minimum fare {MINIMUM_FARE}"
        )


class TestFareBreakdown:
    # TODO: Implement a fare breakdown endpoint
    # def test_fare_breakdown_has_all_components(self):
    #     """Fare breakdown should include base, distance, time, surge, tip, tolls, total."""
    #     pass
    pass


class TestFareEstimation:
    # TODO: Implement fare estimation before trip starts
    # def test_estimate_returns_min_max_range(self):
    #     """Estimate should return a fare range (min/max) based on distance/time."""
    #     pass

    # TODO: Estimation with surge
    # def test_estimate_with_current_surge(self):
    #     """Estimation should include current surge multiplier in range."""
    #     pass
    pass


class TestPromoCode:
    # TODO: Implement promo code support
    # def test_percentage_promo_code(self):
    #     """20% off promo should reduce fare by 20%."""
    #     pass

    # TODO: Fixed amount promo
    # def test_fixed_amount_promo(self):
    #     """$5 off promo should reduce fare by $5."""
    #     pass

    # TODO: Promo max discount cap
    # def test_promo_max_discount_cap(self):
    #     """Percentage promo should have a maximum discount amount."""
    #     pass
    pass
