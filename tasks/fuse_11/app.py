from typing import Callable


class InvalidTransitionError(Exception):
    pass


class StateMachine:
    def __init__(self, initial_state: str) -> None:
        pass

    def add_transition(self, from_state: str, event: str, to_state: str,
                       guard: Callable | None = None) -> None:
        raise NotImplementedError

    def add_on_enter(self, state: str, callback: Callable) -> None:
        raise NotImplementedError

    def add_on_exit(self, state: str, callback: Callable) -> None:
        raise NotImplementedError

    def trigger(self, event: str, **context) -> None:
        raise NotImplementedError

    @property
    def current_state(self) -> str:
        raise NotImplementedError

    def can_trigger(self, event: str) -> bool:
        raise NotImplementedError

    def history(self) -> list[tuple[str, str, str]]:
        raise NotImplementedError
