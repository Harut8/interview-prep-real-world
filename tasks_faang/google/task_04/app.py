"""
URL Router / API Gateway

Routes HTTP request paths to handler functions with support for path parameters,
middleware, and route grouping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class Request:
    """Simplified HTTP request."""
    method: HTTPMethod
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None


@dataclass
class Response:
    """Simplified HTTP response."""
    status_code: int = 200
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)


# Handler and middleware type aliases
Handler = Callable[[Request, dict[str, str]], Response]
Middleware = Callable[[Request, dict[str, str], Handler], Response]


@dataclass
class Route:
    """A registered route with its handler and metadata."""
    pattern: str
    method: HTTPMethod
    handler: Handler
    middleware: list[Middleware] = field(default_factory=list)
    regex: Optional[re.Pattern] = None
    param_names: list[str] = field(default_factory=list)


class Router:
    """URL router with path parameter support."""

    def __init__(self) -> None:
        self.routes: list[Route] = []

    def add_route(
        self,
        method: HTTPMethod,
        pattern: str,
        handler: Handler,
    ) -> None:
        """Register a route pattern with a handler."""
        # BUG #3: No check for duplicate routes — silently overwrites.
        # Should raise an error if the same method+pattern is already registered.
        param_names, regex = self._compile_pattern(pattern)
        route = Route(
            pattern=pattern,
            method=method,
            handler=handler,
            regex=regex,
            param_names=param_names,
        )
        self.routes.append(route)

    def match(self, method: HTTPMethod, path: str) -> Optional[tuple[Route, dict[str, str]]]:
        """Find the route that matches the given method and path."""
        # BUG #1: Returns the first match found, which may be a parameterized route
        # instead of an exact/static match. Should prefer static routes over
        # parameterized ones when both match.
        for route in self.routes:
            if route.method != method:
                continue
            if route.regex is None:
                continue
            m = route.regex.match(path)
            if m:
                params = {}
                for i, name in enumerate(route.param_names):
                    params[name] = m.group(i + 1)
                return route, params
        return None

    def dispatch(self, request: Request) -> Response:
        """Dispatch a request to the matching handler."""
        result = self.match(request.method, request.path)
        if result is None:
            return Response(status_code=404, body={"error": "Not Found"})

        route, params = result
        return route.handler(request, params)

    def _compile_pattern(self, pattern: str) -> tuple[list[str], re.Pattern]:
        """Compile a URL pattern into a regex for matching."""
        param_names: list[str] = []
        regex_parts: list[str] = ["^"]

        parts = pattern.strip("/").split("/")
        for part in parts:
            regex_parts.append("/")
            if part.startswith("{") and part.endswith("}"):
                param_name = part[1:-1]
                param_names.append(param_name)
                # BUG #2: Only matches word characters [a-zA-Z0-9_].
                # Fails for values containing dots, hyphens, or other URL-safe chars.
                # e.g., /files/{filename} won't match /files/my-doc.pdf
                regex_parts.append(r"([a-zA-Z0-9_]+)")
            else:
                regex_parts.append(re.escape(part))

        regex_parts.append("$")
        return param_names, re.compile("".join(regex_parts))

    # -------------------------------------------------------------------------
    # TODO: Implement middleware support
    # -------------------------------------------------------------------------
    def add_route_with_middleware(
        self,
        method: HTTPMethod,
        pattern: str,
        handler: Handler,
        middleware: list[Middleware],
    ) -> None:
        """Register a route with middleware functions that run before the handler."""
        raise NotImplementedError("Middleware support not implemented")

    def dispatch_with_middleware(self, request: Request) -> Response:
        """Dispatch a request, running any middleware before the handler."""
        raise NotImplementedError("Middleware dispatch not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement route groups
    # -------------------------------------------------------------------------
    def group(self, prefix: str) -> "RouteGroup":
        """Create a route group with a shared prefix."""
        raise NotImplementedError("Route groups not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement wildcard routes
    # -------------------------------------------------------------------------
    def add_wildcard_route(
        self,
        method: HTTPMethod,
        pattern: str,
        handler: Handler,
    ) -> None:
        """Register a route with wildcard parameter like /static/{path:*}."""
        raise NotImplementedError("Wildcard routes not implemented")


class RouteGroup:
    """A group of routes sharing a common prefix."""

    def __init__(self, router: Router, prefix: str) -> None:
        self.router = router
        self.prefix = prefix.rstrip("/")

    def add_route(self, method: HTTPMethod, pattern: str, handler: Handler) -> None:
        """Add a route with the group's prefix prepended."""
        full_pattern = f"{self.prefix}{pattern}"
        self.router.add_route(method, full_pattern, handler)
