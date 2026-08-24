# State Machine — Order Lifecycle

**Practical LLD — matches Fuse's "state machine for game loop" prompt.**

Implement a generic state machine, then use it to model an order lifecycle with validation guards.

## Interface

```python
class StateMachine:
    def __init__(self, initial_state: str) -> None: ...
    def add_transition(self, from_state: str, event: str, to_state: str, guard: Callable | None = None) -> None: ...
    def add_on_enter(self, state: str, callback: Callable) -> None: ...
    def add_on_exit(self, state: str, callback: Callable) -> None: ...
    def trigger(self, event: str, **context) -> None: ...
    def current_state(self) -> str: ...
    def can_trigger(self, event: str) -> bool: ...
    def history(self) -> list[tuple[str, str, str]]: ...
```

## Requirements

- `add_transition(from, event, to, guard)` — registers a valid transition. `guard` is an optional callable that returns bool; transition only fires if guard returns True.
- `trigger(event, **context)` — fires the event. Raises `InvalidTransitionError` if no transition exists from current state for this event, or if the guard fails.
- On transition: call `on_exit` of old state, move to new state, call `on_enter` of new state.
- `history()` returns list of `(from_state, event, to_state)` tuples.
- `can_trigger(event)` returns True if the event has a valid transition from current state (ignoring guards).

## Example: Order Lifecycle

```
created → [pay] → paid → [ship] → shipped → [deliver] → delivered
                    ↓                           ↓
               [cancel] → cancelled        [return] → returned
```

## Patterns Tested

State pattern, guard clauses, callbacks/hooks, transition validation.

## Time Target: 40 minutes
