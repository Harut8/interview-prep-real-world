import pytest
from app import GameOfLife


@pytest.fixture
def grid():
    return GameOfLife(5, 5)


class TestBasicState:
    def test_empty_grid(self, grid):
        assert grid.get_live_cells() == set()
        assert grid.get_generation() == 0

    def test_set_alive(self, grid):
        grid.set_alive(1, 1)
        assert grid.is_alive(1, 1) is True

    def test_set_dead(self, grid):
        grid.set_alive(1, 1)
        grid.set_dead(1, 1)
        assert grid.is_alive(1, 1) is False

    def test_load_pattern(self, grid):
        grid.load_pattern([(0, 0), (1, 1), (2, 2)])
        assert grid.get_live_cells() == {(0, 0), (1, 1), (2, 2)}


class TestConwayRules:
    def test_lonely_cell_dies(self, grid):
        grid.set_alive(2, 2)
        grid.step()
        assert grid.is_alive(2, 2) is False

    def test_cell_with_two_neighbors_survives(self, grid):
        grid.load_pattern([(1, 1), (1, 2), (1, 3)])  # horizontal blinker
        grid.step()
        assert grid.is_alive(1, 2) is True  # center survives

    def test_dead_cell_with_three_neighbors_born(self, grid):
        grid.load_pattern([(0, 1), (1, 0), (1, 1)])
        grid.step()
        assert grid.is_alive(0, 0) is True  # has 3 neighbors

    def test_overcrowded_cell_dies(self, grid):
        grid.load_pattern([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)])
        grid.step()
        assert grid.is_alive(1, 1) is False  # 4 neighbors → dies


class TestPatterns:
    def test_blinker_oscillates(self, grid):
        grid.load_pattern([(1, 0), (1, 1), (1, 2)])  # horizontal
        grid.step()
        # Should become vertical
        assert grid.is_alive(0, 1) is True
        assert grid.is_alive(1, 1) is True
        assert grid.is_alive(2, 1) is True
        assert grid.is_alive(1, 0) is False
        assert grid.is_alive(1, 2) is False

    def test_blinker_period_2(self, grid):
        grid.load_pattern([(1, 0), (1, 1), (1, 2)])
        grid.step()
        grid.step()
        assert grid.get_live_cells() == {(1, 0), (1, 1), (1, 2)}
        assert grid.get_generation() == 2

    def test_block_is_stable(self, grid):
        block = [(1, 1), (1, 2), (2, 1), (2, 2)]
        grid.load_pattern(block)
        grid.step()
        assert grid.get_live_cells() == set(block)


class TestGeneration:
    def test_generation_increments(self, grid):
        grid.step()
        grid.step()
        grid.step()
        assert grid.get_generation() == 3
