import pytest
from app import ChargingScheduler, SchedulingError


class TestBasicScheduling:
    def test_single_vehicle(self):
        prices = [10.0, 5.0, 8.0, 3.0, 7.0]
        s = ChargingScheduler(prices)
        s.add_vehicle("EV1", arrival=0, deadline=5, energy_needed=2)
        result = s.schedule()
        assert len(result["EV1"]) == 2
        assert s.total_cost() == 8.0  # hours 3 ($3) + 1 ($5)

    def test_vehicle_charges_cheapest_hours(self):
        prices = [1.0, 100.0, 1.0, 100.0]
        s = ChargingScheduler(prices)
        s.add_vehicle("EV1", arrival=0, deadline=4, energy_needed=2)
        result = s.schedule()
        assert set(result["EV1"]) == {0, 2}
        assert s.total_cost() == 2.0


class TestMultipleVehicles:
    def test_no_conflict(self):
        prices = [5.0] * 10
        s = ChargingScheduler(prices)
        s.add_vehicle("EV1", arrival=0, deadline=5, energy_needed=2)
        s.add_vehicle("EV2", arrival=5, deadline=10, energy_needed=2)
        result = s.schedule()
        assert len(result["EV1"]) == 2
        assert len(result["EV2"]) == 2

    def test_competing_for_cheap_slots(self):
        prices = [1.0, 100.0, 100.0, 100.0]
        s = ChargingScheduler(prices)
        s.add_vehicle("EV1", arrival=0, deadline=4, energy_needed=1)
        s.add_vehicle("EV2", arrival=0, deadline=4, energy_needed=1)
        result = s.schedule()
        # One gets hour 0, the other gets the next cheapest
        all_hours = result["EV1"] + result["EV2"]
        assert 0 in all_hours


class TestEdgeCases:
    def test_impossible_schedule(self):
        prices = [5.0, 5.0]
        s = ChargingScheduler(prices)
        s.add_vehicle("EV1", arrival=0, deadline=2, energy_needed=3)
        with pytest.raises(SchedulingError):
            s.schedule()

    def test_tight_deadline(self):
        prices = [10.0]
        s = ChargingScheduler(prices)
        s.add_vehicle("EV1", arrival=0, deadline=1, energy_needed=1)
        result = s.schedule()
        assert result["EV1"] == [0]
        assert s.total_cost() == 10.0

    def test_zero_energy_needed(self):
        prices = [5.0, 5.0, 5.0]
        s = ChargingScheduler(prices)
        s.add_vehicle("EV1", arrival=0, deadline=3, energy_needed=0)
        result = s.schedule()
        assert result["EV1"] == []
        assert s.total_cost() == 0.0
