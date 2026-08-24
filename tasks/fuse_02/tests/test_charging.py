import pytest
from app import ChargingStationTracker


@pytest.fixture
def tracker():
    t = ChargingStationTracker()
    t.add_station("S1")
    t.add_station("S2")
    return t


class TestBasicStatus:
    def test_station_starts_offline(self, tracker):
        assert tracker.get_available_stations(0) == []

    def test_report_online(self, tracker):
        tracker.report_status("S1", 0, "online")
        assert "S1" in tracker.get_available_stations(0)

    def test_report_offline(self, tracker):
        tracker.report_status("S1", 0, "online")
        tracker.report_status("S1", 10, "offline")
        assert "S1" not in tracker.get_available_stations(10)


class TestUptime:
    def test_fully_online(self, tracker):
        tracker.report_status("S1", 0, "online")
        assert tracker.get_uptime("S1", 0, 100) == 1.0

    def test_fully_offline(self, tracker):
        assert tracker.get_uptime("S1", 0, 100) == 0.0

    def test_half_uptime(self, tracker):
        tracker.report_status("S1", 0, "online")
        tracker.report_status("S1", 50, "offline")
        assert tracker.get_uptime("S1", 0, 100) == 0.5

    def test_uptime_partial_window(self, tracker):
        tracker.report_status("S1", 0, "online")
        tracker.report_status("S1", 50, "offline")
        assert tracker.get_uptime("S1", 25, 75) == 0.5

    def test_multiple_on_off_cycles(self, tracker):
        tracker.report_status("S1", 0, "online")
        tracker.report_status("S1", 10, "offline")
        tracker.report_status("S1", 20, "online")
        tracker.report_status("S1", 30, "offline")
        # 0-10 online (10), 10-20 offline (10), 20-30 online (10), 30-40 offline
        assert tracker.get_uptime("S1", 0, 40) == 0.5


class TestFleetUptime:
    def test_fleet_average(self, tracker):
        tracker.report_status("S1", 0, "online")  # fully online
        # S2 stays offline
        assert tracker.get_fleet_uptime(0, 100) == 0.5

    def test_fleet_all_online(self, tracker):
        tracker.report_status("S1", 0, "online")
        tracker.report_status("S2", 0, "online")
        assert tracker.get_fleet_uptime(0, 100) == 1.0
