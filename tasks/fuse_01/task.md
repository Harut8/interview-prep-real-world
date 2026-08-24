# In-Memory Spreadsheet (LC 631 — Design Excel Sum Formula)

**Priority: #1 — most-reported Fuse interview problem.**

Implement a class `Spreadsheet` that supports cells, formulas, dependency tracking, cycle detection, and undo.

## Interface

```python
class Spreadsheet:
    def __init__(self, rows: int, cols: int) -> None: ...
    def set(self, cell: str, value) -> None: ...
    def get(self, cell: str) -> int | float: ...
    def undo(self) -> None: ...
```

## Requirements (add incrementally — interviewer layers these on)

### Phase 1 — Basic cells
- `set("A1", 5)` stores a numeric value.
- `get("A1")` returns `5`.
- Cells are addressed as column-letter + row-number: A1, B3, Z26.

### Phase 2 — Range SUM
- `set("C1", "=SUM(A1:A10)")` sets C1 to the sum of A1 through A10.
- `get("C1")` evaluates the formula and returns the result.

### Phase 3 — Cell-ref formulas
- `set("B1", "=A1+A2")` — formulas can reference individual cells.
- Support `+`, `-`, `*`, and literal numbers in formulas.

### Phase 4 — Dependency graph (DAG)
- When A1 changes, all cells that depend on A1 must recalculate.
- Multi-level chains: if C1 depends on B1 which depends on A1, updating A1 recalculates B1 then C1 (topological order).

### Phase 5 — Circular dependency detection
- `set("A1", "=B1")` then `set("B1", "=A1")` → raise `CircularDependencyError`.
- Detect before applying the change (don't corrupt state).

### Phase 6 — Undo
- `undo()` reverts the last `set` operation (value + formula + dependency edges).
- Multiple undos walk back through history.

### Phase 7 — Caching
- `get()` should not re-evaluate a formula if none of its dependencies changed.
- Invalidate cache only along the dependency chain when a cell updates.

## Patterns Tested

Hash maps, DAG, topological sort, DFS cycle detection, memoization/caching, expression parsing, Command pattern (undo).

## What You Should Do

1. Write tests first — cover each phase.
2. Implement incrementally: get Phase 1 working before Phase 2.
3. Narrate every design choice out loud.

## Time Target: 60 minutes
