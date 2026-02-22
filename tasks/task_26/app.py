from collections.abc import Callable
from typing import Any


class EventEmitter:
    """Event emitter supporting named events with multiple listeners."""

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}
        self._max_listeners: int = 10

    def on(self, event: str, listener: Callable) -> "EventEmitter":
        """Register a listener for an event."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)
        return self

    def off(self, event: str, listener: Callable) -> "EventEmitter":
        """Remove a listener for an event."""
        if event not in self._listeners:
            return self

        # BUG: remove() only removes first occurrence
        # If listener registered twice, second copy remains
        self._listeners[event].remove(listener)
        return self

    def emit(self, event: str, *args: Any, **kwargs: Any) -> bool:
        """Emit an event, calling all registered listeners."""
        if event not in self._listeners:
            return False

        # BUG: if one listener raises, subsequent listeners don't run
        for listener in self._listeners[event]:
            listener(*args, **kwargs)

        return True

    def once(self, event: str, listener: Callable) -> "EventEmitter":
        """Register a listener that fires only once."""

        # BUG: wrapper function can't be removed with off() because
        # the caller doesn't have a reference to the wrapper
        def wrapper(*args, **kwargs):
            listener(*args, **kwargs)
            self.off(event, wrapper)

        self.on(event, wrapper)
        return self

    def listeners(self, event: str) -> list[Callable]:
        """Return list of listeners for an event."""
        # BUG: returns the internal list — caller can mutate it
        return self._listeners.get(event, [])

    def listener_count(self, event: str) -> int:
        """Return the number of listeners for an event."""
        return len(self._listeners.get(event, []))

    def remove_all_listeners(self, event: str | None = None) -> "EventEmitter":
        """Remove all listeners, optionally for a specific event."""
        if event is None:
            self._listeners.clear()
        elif event in self._listeners:
            del self._listeners[event]
        return self

    def event_names(self) -> list[str]:
        """Return list of events that have listeners."""
        return [e for e, listeners in self._listeners.items() if listeners]


# TODO: Add prepend_listener(event, listener) method
# TODO: Add wildcard "*" event support
# TODO: Add wait_for(event) returning an asyncio Future
# TODO: Add pipe(target_emitter, events) method
# TODO: Add max listeners warning
