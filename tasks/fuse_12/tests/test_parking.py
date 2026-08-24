import pytest
from app import ParkingLot, Vehicle


@pytest.fixture
def lot():
    return ParkingLot(small=2, medium=2, large=1)


class TestParking:
    def test_park_small(self, lot):
        v = Vehicle("ABC123", "small")
        ticket = lot.park(v)
        assert ticket is not None

    def test_park_returns_none_when_full(self, lot):
        for i in range(5):
            lot.park(Vehicle(f"PLATE{i}", "small"))
        result = lot.park(Vehicle("EXTRA", "small"))
        assert result is None

    def test_no_duplicate_plates(self, lot):
        v = Vehicle("ABC123", "small")
        lot.park(v)
        result = lot.park(Vehicle("ABC123", "small"))
        assert result is None

    def test_large_vehicle_only_fits_large_spot(self, lot):
        v = Vehicle("TRUCK1", "large")
        ticket = lot.park(v)
        assert ticket is not None
        v2 = Vehicle("TRUCK2", "large")
        assert lot.park(v2) is None  # only 1 large spot

    def test_small_can_use_larger_spot(self, lot):
        # Fill small spots
        lot.park(Vehicle("S1", "small"))
        lot.park(Vehicle("S2", "small"))
        # Next small should go into medium
        ticket = lot.park(Vehicle("S3", "small"))
        assert ticket is not None


class TestUnpark:
    def test_unpark_frees_spot(self, lot):
        v = Vehicle("ABC123", "small")
        ticket = lot.park(v)
        before = lot.available_spots()
        lot.unpark(ticket)
        after = lot.available_spots()
        assert after == before + 1

    def test_unpark_returns_cost(self, lot):
        v = Vehicle("ABC123", "small")
        ticket = lot.park(v)
        cost = lot.unpark(ticket)
        assert isinstance(cost, (int, float))
        assert cost >= 0

    def test_unpark_invalid_ticket(self, lot):
        with pytest.raises(Exception):
            lot.unpark("INVALID")


class TestAvailableSpots:
    def test_initial_count(self, lot):
        assert lot.available_spots() == 5  # 2+2+1

    def test_filtered_count(self, lot):
        assert lot.available_spots("small") == 2
        assert lot.available_spots("large") == 1

    def test_count_decreases_on_park(self, lot):
        lot.park(Vehicle("V1", "small"))
        assert lot.available_spots("small") == 1
