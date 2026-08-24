import pytest
from app import Elevator, ElevatorSystem


class TestSingleElevator:
    def test_starts_at_ground(self):
        e = Elevator(0, 10)
        assert e.current_floor == 0
        assert e.is_idle is True

    def test_moves_toward_destination(self):
        e = Elevator(0, 10)
        e.add_destination(3)
        e.step()
        assert e.current_floor == 1
        assert e.direction == "up"

    def test_arrives_at_destination(self):
        e = Elevator(0, 10)
        e.add_destination(2)
        e.step()
        e.step()
        assert e.current_floor == 2
        assert e.is_idle is True

    def test_multiple_destinations_scan(self):
        e = Elevator(0, 10)
        e.add_destination(5)
        e.add_destination(3)
        # Should visit 3 first (on the way up), then 5
        for _ in range(3):
            e.step()
        assert e.current_floor == 3


class TestElevatorSystem:
    def test_single_request(self):
        sys = ElevatorSystem(num_elevators=1, num_floors=10)
        sys.request(floor=3, direction="up")
        for _ in range(3):
            sys.step()
        states = sys.get_elevator_states()
        assert states[0]["floor"] == 3

    def test_assigns_nearest_idle(self):
        sys = ElevatorSystem(num_elevators=2, num_floors=10)
        # Move elevator 0 to floor 5
        sys.request(floor=5, direction="up")
        for _ in range(5):
            sys.step()
        # Now request floor 4 — elevator 0 (at 5) is closer than elevator 1 (at 0)
        sys.request(floor=4, direction="down")
        sys.step()
        states = sys.get_elevator_states()
        # Elevator 0 should handle this (was at 5, now at 4)
        assert states[0]["floor"] == 4

    def test_multiple_requests(self):
        sys = ElevatorSystem(num_elevators=2, num_floors=10)
        sys.request(floor=2, direction="up")
        sys.request(floor=8, direction="down")
        for _ in range(8):
            sys.step()
        states = sys.get_elevator_states()
        floors = {s["floor"] for s in states}
        assert 2 in floors or 8 in floors
