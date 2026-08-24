class SchedulingError(Exception):
    pass


class ChargingScheduler:
    def __init__(self, prices: list[float]) -> None:
        pass

    def add_vehicle(self, vehicle_id: str, arrival: int, deadline: int, energy_needed: float) -> None:
        raise NotImplementedError

    def schedule(self) -> dict[str, list[int]]:
        raise NotImplementedError

    def total_cost(self) -> float:
        raise NotImplementedError
