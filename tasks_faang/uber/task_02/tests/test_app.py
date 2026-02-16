"""
Tests for Surge Pricing Calculator.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import time
from app import (
    Location,
    Zone,
    ZoneState,
    zones,
    zone_states,
    surge_history,
    haversine_distance,
    find_zone_for_location,
    calculate_surge_multiplier,
    get_surge_price,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all in-memory state before each test."""
    zones.clear()
    zone_states.clear()
    surge_history.clear()
    yield
    zones.clear()
    zone_states.clear()
    surge_history.clear()


def _create_zone(zone_id: str, lat: float, lon: float, radius_km: float,
                 base_fare: float = 5.0, demand: int = 0, supply: int = 0) -> Zone:
    zone = Zone(
        zone_id=zone_id,
        name=f"Zone {zone_id}",
        center=Location(latitude=lat, longitude=lon),
        radius_km=radius_km,
        base_fare=base_fare,
    )
    zones[zone_id] = zone
    zone_states[zone_id] = ZoneState(
        zone_id=zone_id,
        demand_count=demand,
        supply_count=supply,
    )
    return zone


class TestSurgeCalculation:
    def test_normal_conditions_no_surge(self):
        """This test should PASS — equal supply and demand = 1.0x."""
        _create_zone("z1", 37.77, -122.41, 5.0, demand=10, supply=10)
        multiplier = calculate_surge_multiplier("z1")
        assert multiplier == pytest.approx(1.0)

    def test_high_demand_produces_surge(self):
        """This test should PASS — more demand than supply."""
        _create_zone("z1", 37.77, -122.41, 5.0, demand=30, supply=10)
        multiplier = calculate_surge_multiplier("z1")
        assert multiplier == pytest.approx(3.0)

    def test_zero_supply_should_not_crash(self):
        """
        FAILING: When supply is zero, should return max surge,
        not crash with ZeroDivisionError.
        """
        _create_zone("z1", 37.77, -122.41, 5.0, demand=20, supply=0)
        # Should NOT raise, should return a max multiplier
        multiplier = calculate_surge_multiplier("z1")
        assert multiplier >= 1.0

    def test_surge_multiplier_should_be_capped(self):
        """
        FAILING: Multiplier should not exceed max cap (5.0x).
        Currently demand=100, supply=1 gives 100x.
        """
        _create_zone("z1", 37.77, -122.41, 5.0, demand=100, supply=1)
        multiplier = calculate_surge_multiplier("z1")
        assert multiplier <= 5.0, f"Multiplier {multiplier} exceeds cap of 5.0"


class TestZoneLookup:
    def test_location_in_zone(self):
        """This test should PASS — point inside zone."""
        _create_zone("downtown", 37.7749, -122.4194, 3.0)
        loc = Location(latitude=37.775, longitude=-122.420)
        zone = find_zone_for_location(loc)
        assert zone is not None
        assert zone.zone_id == "downtown"

    def test_overlapping_zones_picks_most_specific(self):
        """
        FAILING: When a location is in both a large and small zone,
        should return the smallest (most specific) zone.
        """
        _create_zone("city_wide", 37.7749, -122.4194, 20.0)
        _create_zone("downtown", 37.7749, -122.4194, 3.0)

        loc = Location(latitude=37.775, longitude=-122.420)
        zone = find_zone_for_location(loc)
        # Should pick "downtown" (smaller, more specific)
        assert zone.zone_id == "downtown"


class TestSurgePrice:
    def test_surged_fare_calculation(self):
        """This test should PASS — fare * multiplier."""
        _create_zone("z1", 37.77, -122.41, 5.0, base_fare=10.0,
                     demand=20, supply=10)
        result = get_surge_price("z1")
        assert result["multiplier"] == 2.0
        assert result["surged_fare"] == 20.0


class TestPriceSmoothing:
    # TODO: Implement exponential smoothing for surge multiplier
    # def test_smoothing_gradual_increase(self):
    #     """Multiplier should increase gradually, not jump immediately."""
    #     pass

    # TODO: Smoothing factor configuration
    # def test_smoothing_factor_alpha(self):
    #     """With alpha=0.3, new = 0.3 * calculated + 0.7 * previous."""
    #     pass
    pass


class TestHistoricalPricing:
    # TODO: Implement historical pricing query
    # def test_query_surge_history_by_time_range(self):
    #     """Should return all surge records for a zone within a time range."""
    #     pass

    # TODO: History aggregation
    # def test_average_surge_over_period(self):
    #     """Should calculate average surge multiplier over a time period."""
    #     pass
    pass
