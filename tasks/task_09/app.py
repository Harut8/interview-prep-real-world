from collections import defaultdict
from typing import Any, Callable


class EventEmitter:
    """Simple event emitter / pub-sub system."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, handler: Callable) -> None:
        """Subscribe a handler to an event."""
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Callable) -> None:
        """Unsubscribe a handler from an event."""
        if event in self._handlers:
            self._handlers[event].remove(handler)

    def once(self, event: str, handler: Callable) -> None:
        """Subscribe a handler that only fires once."""
        def wrapper(*args, **kwargs):
            handler(*args, **kwargs)
            # BUG: this tries to remove 'handler' but 'wrapper' was registered
            self.off(event, handler)
        self.on(event, wrapper)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event, calling all subscribed handlers."""
        if event not in self._handlers:
            return
        # BUG: if a handler calls off() during iteration, RuntimeError
        for handler in self._handlers[event]:
            # BUG: exception in one handler stops the rest
            handler(*args, **kwargs)

    def listeners(self, event: str) -> list[Callable]:
        """Return list of handlers for an event."""
        return self._handlers.get(event, [])

    def remove_all(self, event: str | None = None) -> None:
        """Remove all handlers for an event (or all events if None)."""
        if event:
            self._handlers.pop(event, None)
        else:
            self._handlers.clear()

# Usage example
emitter = EventEmitter()

# Subscribe to an event
def handle_event(data):
    print(f"Event received: {data}")

emitter.on("my_event", handle_event)
# Emit an event
emitter.emit("my_event", data="Hello, world!")

# TODO: Add async handler support
# TODO: Add event history tracking
