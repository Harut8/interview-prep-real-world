# Grid Game — Conway's Game of Life

**Practical LLD — matches Fuse's "grid-based game engine with real-time state" prompt.**

Implement Conway's Game of Life as a clean class with extensible rules.

## Interface

```python
class GameOfLife:
    def __init__(self, rows: int, cols: int) -> None: ...
    def set_alive(self, row: int, col: int) -> None: ...
    def set_dead(self, row: int, col: int) -> None: ...
    def is_alive(self, row: int, col: int) -> bool: ...
    def step(self) -> None: ...
    def get_generation(self) -> int: ...
    def get_live_cells(self) -> set[tuple[int, int]]: ...
    def load_pattern(self, cells: list[tuple[int, int]]) -> None: ...
```

## Requirements

### Core rules (standard Conway)
- Any live cell with 2 or 3 neighbors survives.
- Any dead cell with exactly 3 neighbors becomes alive.
- All other cells die or stay dead.
- `step()` advances one generation — all births/deaths happen simultaneously.

### Extensions (add when asked)
- **Toroidal wrapping**: edges wrap around (top connects to bottom, left to right).
- **Custom rules**: accept birth/survival counts as parameters (e.g., HighLife: B36/S23).
- **History**: track previous states, detect if the board has stabilized (period-1 or period-2 oscillation).
- **Resize**: dynamically grow the board if a live cell would appear out of bounds.

## Patterns Tested

2D grid state management, neighbor calculation, simultaneous update (double buffer), Strategy pattern (rules).

## Time Target: 45 minutes
