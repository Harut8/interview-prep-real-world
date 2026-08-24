class CircularDependencyError(Exception):
    pass


class Spreadsheet:
    def __init__(self, rows: int, cols: int) -> None:
        pass

    def set(self, cell: str, value) -> None:
        raise NotImplementedError

    def get(self, cell: str) -> int | float:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError
