import pytest
from app import Spreadsheet, CircularDependencyError


@pytest.fixture
def sheet():
    return Spreadsheet(26, 26)


# --- Phase 1: Basic cells ---

class TestBasicCells:
    def test_set_and_get(self, sheet):
        sheet.set("A1", 5)
        assert sheet.get("A1") == 5

    def test_overwrite(self, sheet):
        sheet.set("A1", 5)
        sheet.set("A1", 10)
        assert sheet.get("A1") == 10

    def test_empty_cell_returns_zero(self, sheet):
        assert sheet.get("A1") == 0

    def test_multiple_cells(self, sheet):
        sheet.set("A1", 1)
        sheet.set("B2", 2)
        sheet.set("C3", 3)
        assert sheet.get("A1") == 1
        assert sheet.get("B2") == 2
        assert sheet.get("C3") == 3


# --- Phase 2: Range SUM ---

class TestRangeSum:
    def test_sum_column(self, sheet):
        for i in range(1, 6):
            sheet.set(f"A{i}", i)
        sheet.set("B1", "=SUM(A1:A5)")
        assert sheet.get("B1") == 15

    def test_sum_empty_range(self, sheet):
        sheet.set("B1", "=SUM(A1:A5)")
        assert sheet.get("B1") == 0

    def test_sum_single_cell_range(self, sheet):
        sheet.set("A1", 42)
        sheet.set("B1", "=SUM(A1:A1)")
        assert sheet.get("B1") == 42

    def test_sum_rectangular_range(self, sheet):
        sheet.set("A1", 1)
        sheet.set("A2", 2)
        sheet.set("B1", 3)
        sheet.set("B2", 4)
        sheet.set("C1", "=SUM(A1:B2)")
        assert sheet.get("C1") == 10


# --- Phase 3: Cell-ref formulas ---

class TestFormulas:
    def test_add_two_cells(self, sheet):
        sheet.set("A1", 10)
        sheet.set("A2", 20)
        sheet.set("B1", "=A1+A2")
        assert sheet.get("B1") == 30

    def test_subtract(self, sheet):
        sheet.set("A1", 50)
        sheet.set("A2", 20)
        sheet.set("B1", "=A1-A2")
        assert sheet.get("B1") == 30

    def test_multiply(self, sheet):
        sheet.set("A1", 6)
        sheet.set("A2", 7)
        sheet.set("B1", "=A1*A2")
        assert sheet.get("B1") == 42

    def test_cell_plus_literal(self, sheet):
        sheet.set("A1", 10)
        sheet.set("B1", "=A1+5")
        assert sheet.get("B1") == 15

    def test_complex_formula(self, sheet):
        sheet.set("A1", 2)
        sheet.set("A2", 3)
        sheet.set("A3", 4)
        sheet.set("B1", "=A1+A2*A3")
        # Depends on whether you implement operator precedence
        # With precedence: 2 + 3*4 = 14
        # Without (left-to-right): (2+3)*4 = 20
        result = sheet.get("B1")
        assert result in (14, 20)


# --- Phase 4: Dependency propagation ---

class TestDependencyPropagation:
    def test_update_propagates(self, sheet):
        sheet.set("A1", 5)
        sheet.set("B1", "=A1+10")
        assert sheet.get("B1") == 15
        sheet.set("A1", 20)
        assert sheet.get("B1") == 30

    def test_chain_propagation(self, sheet):
        sheet.set("A1", 1)
        sheet.set("B1", "=A1+1")   # B1 = 2
        sheet.set("C1", "=B1+1")   # C1 = 3
        assert sheet.get("C1") == 3
        sheet.set("A1", 10)
        assert sheet.get("B1") == 11
        assert sheet.get("C1") == 12

    def test_diamond_dependency(self, sheet):
        sheet.set("A1", 1)
        sheet.set("B1", "=A1+1")   # 2
        sheet.set("C1", "=A1+2")   # 3
        sheet.set("D1", "=B1+C1")  # 5
        assert sheet.get("D1") == 5
        sheet.set("A1", 10)
        assert sheet.get("D1") == 23  # (10+1) + (10+2) = 23

    def test_sum_propagates_on_update(self, sheet):
        sheet.set("A1", 1)
        sheet.set("A2", 2)
        sheet.set("B1", "=SUM(A1:A2)")
        assert sheet.get("B1") == 3
        sheet.set("A1", 10)
        assert sheet.get("B1") == 12


# --- Phase 5: Circular dependency detection ---

class TestCircularDependency:
    def test_direct_cycle(self, sheet):
        sheet.set("A1", "=B1")
        with pytest.raises(CircularDependencyError):
            sheet.set("B1", "=A1")

    def test_self_reference(self, sheet):
        with pytest.raises(CircularDependencyError):
            sheet.set("A1", "=A1")

    def test_indirect_cycle(self, sheet):
        sheet.set("A1", "=B1")
        sheet.set("B1", "=C1")
        with pytest.raises(CircularDependencyError):
            sheet.set("C1", "=A1")

    def test_state_not_corrupted_after_cycle(self, sheet):
        sheet.set("A1", 5)
        sheet.set("B1", "=A1")
        with pytest.raises(CircularDependencyError):
            sheet.set("A1", "=B1")
        assert sheet.get("A1") == 5
        assert sheet.get("B1") == 5


# --- Phase 6: Undo ---

class TestUndo:
    def test_undo_set(self, sheet):
        sheet.set("A1", 5)
        sheet.set("A1", 10)
        sheet.undo()
        assert sheet.get("A1") == 5

    def test_undo_to_empty(self, sheet):
        sheet.set("A1", 5)
        sheet.undo()
        assert sheet.get("A1") == 0

    def test_undo_formula(self, sheet):
        sheet.set("A1", 5)
        sheet.set("B1", "=A1+10")
        sheet.undo()
        assert sheet.get("B1") == 0

    def test_undo_restores_dependencies(self, sheet):
        sheet.set("A1", 5)
        sheet.set("B1", "=A1+10")
        sheet.undo()  # removes B1 formula
        sheet.set("A1", 20)
        assert sheet.get("B1") == 0  # B1 no longer depends on A1

    def test_multiple_undos(self, sheet):
        sheet.set("A1", 1)
        sheet.set("A1", 2)
        sheet.set("A1", 3)
        sheet.undo()
        assert sheet.get("A1") == 2
        sheet.undo()
        assert sheet.get("A1") == 1


# --- Phase 7: Caching ---

class TestCaching:
    def test_repeated_get_no_recompute(self, sheet):
        sheet.set("A1", 5)
        sheet.set("B1", "=A1+10")
        assert sheet.get("B1") == 15
        assert sheet.get("B1") == 15  # should use cache

    def test_cache_invalidation_on_update(self, sheet):
        sheet.set("A1", 5)
        sheet.set("B1", "=A1+10")
        assert sheet.get("B1") == 15
        sheet.set("A1", 20)
        assert sheet.get("B1") == 30  # cache invalidated
