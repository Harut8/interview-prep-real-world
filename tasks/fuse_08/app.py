class GameOfLife:
    def __init__(self, rows: int, cols: int) -> None:
        pass

    def set_alive(self, row: int, col: int) -> None:
        raise NotImplementedError

    def set_dead(self, row: int, col: int) -> None:
        raise NotImplementedError

    def is_alive(self, row: int, col: int) -> bool:
        raise NotImplementedError

    def step(self) -> None:
        raise NotImplementedError

    def get_generation(self) -> int:
        raise NotImplementedError

    def get_live_cells(self) -> set[tuple[int, int]]:
        raise NotImplementedError

    def load_pattern(self, cells: list[tuple[int, int]]) -> None:
        raise NotImplementedError
