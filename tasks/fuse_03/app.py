class CarbonTracker:
    def __init__(self) -> None:
        pass

    def add_offset(self, start: int, end: int, kg_co2_per_hour: float) -> None:
        raise NotImplementedError

    def total_savings(self, start: int, end: int) -> float:
        raise NotImplementedError

    def peak_offset_rate(self, start: int, end: int) -> float:
        raise NotImplementedError

    def snapshot(self, timestamp: int) -> float:
        raise NotImplementedError
