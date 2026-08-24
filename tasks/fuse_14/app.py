class Elevator:
    def __init__(self, elevator_id: int, num_floors: int) -> None:
        pass

    def add_destination(self, floor: int) -> None:
        raise NotImplementedError

    def step(self) -> None:
        raise NotImplementedError

    @property
    def current_floor(self) -> int:
        raise NotImplementedError

    @property
    def direction(self) -> str:
        raise NotImplementedError

    @property
    def is_idle(self) -> bool:
        raise NotImplementedError


class ElevatorSystem:
    def __init__(self, num_elevators: int, num_floors: int) -> None:
        pass

    def request(self, floor: int, direction: str) -> None:
        raise NotImplementedError

    def step(self) -> None:
        raise NotImplementedError

    def get_elevator_states(self) -> list[dict]:
        raise NotImplementedError
