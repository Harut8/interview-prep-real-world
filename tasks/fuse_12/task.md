# Parking Lot

**Classic OOP warmup — tests clean class hierarchy and extensibility.**

Design and implement a parking lot system.

## Interface

```python
class ParkingLot:
    def __init__(self, small: int, medium: int, large: int) -> None: ...
    def park(self, vehicle: Vehicle) -> str | None: ...
    def unpark(self, ticket: str) -> float: ...
    def available_spots(self, size: str = None) -> int: ...

class Vehicle:
    def __init__(self, plate: str, size: str) -> None: ...
```

## Requirements

- Three spot sizes: `"small"`, `"medium"`, `"large"`.
- A vehicle can park in a spot of its own size or larger (small car in large spot = ok).
- `park(vehicle)` returns a ticket string, or `None` if no suitable spot is available.
- `unpark(ticket)` frees the spot and returns the cost. Cost = hours parked * rate_per_hour (rate varies by spot size).
- `available_spots(size)` returns count of free spots (optionally filtered by size).
- No duplicate plates allowed (same car can't park twice).

## Extensions (add when asked)

- **Handicap spots**: reserved spots that only certain vehicles can use.
- **EV charging spots**: spots with chargers, higher rate.
- **Valet mode**: parking lot assigns optimal spot (smallest available that fits).
- **Peak pricing**: rate multiplier during certain hours.

## Patterns Tested

Inheritance/composition, encapsulation, Single Responsibility, Open/Closed (extending spot types).

## Time Target: 35 minutes
