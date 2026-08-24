class Vehicle:
    def __init__(self, plate: str, size: str) -> None:
        pass


class ParkingLot:
    def __init__(self, small: int, medium: int, large: int) -> None:
        pass

    def park(self, vehicle: Vehicle) -> str | None:
        raise NotImplementedError

    def unpark(self, ticket: str) -> float:
        raise NotImplementedError

    def available_spots(self, size: str = None) -> int:
        raise NotImplementedError
