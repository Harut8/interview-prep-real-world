import pytest
from app import IntervalManager, Interval


@pytest.fixture
def manager():
    return IntervalManager()


def test_basic_intersection(manager):
    a = [Interval(1, 4), Interval(5, 8)]
    b = [Interval(2, 6)]
    result = manager.find_intersections(a, b)
    assert len(result) == 2
    assert result[0].start == 2 and result[0].end == 4
    assert result[1].start == 5 and result[1].end == 6


# FAILS — fix: containment case (one interval fully inside another)
def test_intersection_containment(manager):
    a = [Interval(1, 10)]
    b = [Interval(3, 5)]
    result = manager.find_intersections(a, b)
    assert len(result) == 1
    assert result[0].start == 3 and result[0].end == 5


def test_no_intersection(manager):
    a = [Interval(1, 2)]
    b = [Interval(3, 4)]
    result = manager.find_intersections(a, b)
    assert result == []


def test_merge_overlapping(manager):
    intervals = [Interval(1, 3), Interval(2, 5), Interval(7, 10)]
    result = manager.merge_intervals(intervals)
    assert len(result) == 2
    assert result[0].start == 1 and result[0].end == 5
    assert result[1].start == 7 and result[1].end == 10


# FAILS — fix: adjacent intervals should merge
def test_merge_adjacent(manager):
    intervals = [Interval(1, 3), Interval(3, 5)]
    result = manager.merge_intervals(intervals)
    assert len(result) == 1
    assert result[0].start == 1 and result[0].end == 5


def test_merge_empty(manager):
    result = manager.merge_intervals([])
    assert result == []


def test_insert_interval(manager):
    intervals = [Interval(1, 3), Interval(6, 8)]
    result = manager.insert_interval(intervals, Interval(4, 5))
    assert len(result) == 3


def test_insert_interval_with_merge(manager):
    intervals = [Interval(1, 3), Interval(6, 8)]
    result = manager.insert_interval(intervals, Interval(2, 7))
    assert len(result) == 1
    assert result[0].start == 1 and result[0].end == 8


def test_point_in_interval(manager):
    intervals = [Interval(1, 5), Interval(10, 15)]
    assert manager.is_point_in_any(intervals, 3) is True
    assert manager.is_point_in_any(intervals, 7) is False
    assert manager.is_point_in_any(intervals, 10) is True


def test_total_coverage(manager):
    intervals = [Interval(1, 3), Interval(2, 5), Interval(7, 10)]
    assert manager.total_coverage(intervals) == 7.0  # [1,5] + [7,10] = 4 + 3


def test_empty_intervals(manager):
    assert manager.find_intersections([], []) == []
    assert manager.total_coverage([]) == 0.0


# TODO: Add tests for subtract
# TODO: Add tests for union
# TODO: Add tests for gaps
# TODO: Add tests for IntervalTree
