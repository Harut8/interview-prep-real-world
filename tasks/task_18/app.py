from typing import Any, Callable
from dataclasses import dataclass, field


@dataclass
class Request:
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None


@dataclass
class Response:
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None


class Middleware:
    """Base middleware class."""

    def process_request(self, request: Request) -> Request | Response:
        """Process request. Return Request to continue or Response to short-circuit."""
        return request

    def process_response(self, request: Request, response: Response) -> Response:
        """Process response on the way back."""
        return response


class MiddlewareChain:
    """Chain of middleware that processes requests."""

    def __init__(self):
        self.middlewares: list[Middleware] = []
        self._handler: Callable[[Request], Response] | None = None

    def add(self, middleware: Middleware) -> "MiddlewareChain":
        """Add a middleware to the chain."""
        # BUG: no validation that middleware is actually a Middleware instance
        self.middlewares.append(middleware)
        return self

    def set_handler(self, handler: Callable[[Request], Response]) -> None:
        """Set the final request handler."""
        self._handler = handler

    def handle(self, request: Request) -> Response:
        """Process a request through the middleware chain."""
        if not self._handler:
            raise RuntimeError("No handler set")

        # Process request through middlewares
        # BUG: reversed order — last added runs first
        processed_request = request
        executed_middlewares = []

        for mw in reversed(self.middlewares):
            result = mw.process_request(processed_request)
            if isinstance(result, Response):
                # Short-circuit: return response without calling handler
                return result
            processed_request = result
            executed_middlewares.append(mw)

        # Call the actual handler
        # BUG: if handler raises, response middlewares don't run
        response = self._handler(processed_request)

        # Process response back through middlewares (reverse order)
        for mw in reversed(executed_middlewares):
            response = mw.process_response(processed_request, response)

        return response


def echo_handler(request: Request) -> Response:
    """Simple handler that echoes the request."""
    return Response(
        status_code=200,
        body={"method": request.method, "path": request.path},
    )


# TODO: Add TimingMiddleware
# TODO: Add AuthMiddleware
# TODO: Add LoggingMiddleware
