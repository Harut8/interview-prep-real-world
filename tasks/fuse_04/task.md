# EV Smart Charging Scheduler

**Energy-domain flavor — maps to LC 1353 Max Events / greedy interval scheduling.**

Implement a scheduler that charges EVs by their deadlines at minimum electricity cost, given time-varying prices.

## Interface

```python
class ChargingScheduler:
    def __init__(self, prices: list[float]) -> None: ...
    def add_vehicle(self, vehicle_id: str, arrival: int, deadline: int, energy_needed: float) -> None: ...
    def schedule(self) -> dict[str, list[int]]: ...
    def total_cost(self) -> float: ...
```

## Requirements

- `prices` is a list where `prices[t]` is the electricity cost per kWh at hour `t`.
- `add_vehicle(id, arrival, deadline, energy_needed)` — vehicle arrives at hour `arrival`, must be fully charged by hour `deadline`, needs `energy_needed` kWh.
- Each hour, each vehicle can charge at most 1 kWh. A charger can serve one vehicle per hour.
- `schedule()` returns a dict mapping vehicle_id to a list of hours when it charges. All vehicles must be charged by their deadlines (raise if impossible).
- `total_cost()` returns the sum of `prices[hour]` for all scheduled charging hours.
- Minimize total cost.

## Patterns Tested

Greedy scheduling, priority queues, interval constraints, cost optimization.

## What You Should Do

1. Write tests first.
2. Think greedy: at each hour, which vehicle should charge?

## Time Target: 45 minutes
