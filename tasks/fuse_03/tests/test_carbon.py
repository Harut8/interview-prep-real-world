import pytest
from app import CarbonTracker


@pytest.fixture
def tracker():
    return CarbonTracker()


class TestBasic:
    def test_single_offset_total(self, tracker):
        tracker.add_offset(0, 10, 5.0)  # 5 kg/hr for 10 hours = 50
        assert tracker.total_savings(0, 10) == 50.0

    def test_single_offset_partial_window(self, tracker):
        tracker.add_offset(0, 10, 5.0)
        assert tracker.total_savings(2, 8) == 30.0  # 5 * 6

    def test_snapshot(self, tracker):
        tracker.add_offset(0, 10, 5.0)
        assert tracker.snapshot(5) == 5.0
        assert tracker.snapshot(15) == 0.0

    def test_no_offsets(self, tracker):
        assert tracker.total_savings(0, 100) == 0.0
        assert tracker.snapshot(50) == 0.0


class TestOverlapping:
    def test_stacking(self, tracker):
        tracker.add_offset(0, 10, 3.0)
        tracker.add_offset(5, 15, 2.0)
        assert tracker.snapshot(7) == 5.0  # both active
        assert tracker.snapshot(3) == 3.0  # only first
        assert tracker.snapshot(12) == 2.0  # only second

    def test_stacking_total(self, tracker):
        tracker.add_offset(0, 10, 3.0)   # 3 * 10 = 30
        tracker.add_offset(5, 15, 2.0)   # 2 * 10 = 20
        # 0-5: 3/hr (15), 5-10: 5/hr (25), 10-15: 2/hr (10) = 50
        assert tracker.total_savings(0, 15) == 50.0

    def test_peak_rate(self, tracker):
        tracker.add_offset(0, 10, 3.0)
        tracker.add_offset(5, 15, 2.0)
        assert tracker.peak_offset_rate(0, 15) == 5.0

    def test_peak_rate_in_subwindow(self, tracker):
        tracker.add_offset(0, 10, 3.0)
        tracker.add_offset(5, 15, 2.0)
        assert tracker.peak_offset_rate(0, 4) == 3.0


class TestEdgeCases:
    def test_zero_length_interval(self, tracker):
        tracker.add_offset(0, 10, 5.0)
        assert tracker.total_savings(5, 5) == 0.0

    def test_non_overlapping_query(self, tracker):
        tracker.add_offset(0, 10, 5.0)
        assert tracker.total_savings(20, 30) == 0.0

    def test_many_offsets(self, tracker):
        for i in range(100):
            tracker.add_offset(i, i + 10, 1.0)
        assert tracker.snapshot(50) == 10.0  # 10 overlapping at any mid point
