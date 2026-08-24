# Elevator System

**Classic OOP warmup — event-driven state + scheduling algorithm.**

## Interface

```python
class ElevatorSystem:
    def __init__(self, num_elevators: int, num_floors: int) -> None: ...
    def request(self, floor: int, direction: str) -> None: ...
    def step(self) -> None: ...
    def get_elevator_states(self) -> list[dict]: ...

class Elevator:
    def __init__(self, elevator_id: int, num_floors: int) -> None: ...
    def add_destination(self, floor: int) -> None: ...
    def step(self) -> None: ...
    def current_floor(self) -> int: ...
    def direction(self) -> str: ...
    def is_idle(self) -> bool: ...
```

## Requirements

- `request(floor, direction)` — a person on `floor` wants to go `direction` ("up" or "down"). System assigns the best elevator.
- `step()` — advances simulation by one time unit. Each elevator moves one floor per step.
- Elevator picks up passengers along the way (SCAN/elevator algorithm).
- `get_elevator_states()` returns list of `{"id": int, "floor": int, "direction": str, "destinations": list}`.
- Dispatching strategy: assign to nearest elevator heading in the right direction, or nearest idle elevator.

## Extensions

- **Express elevators**: serve only certain floors.
- **Weight capacity**: reject if overloaded.
- **VIP priority**: certain requests jump the queue.
- **Energy optimization**: prefer idle elevators on nearby floors.

## Time Target: 45 minutes
