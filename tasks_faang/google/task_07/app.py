"""
Load Balancer

Distribute requests across backend servers with support for multiple strategies,
health checking, and circuit breaking.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class ServerStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"


class Strategy(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"


@dataclass
class Server:
    """A backend server."""
    server_id: str
    host: str
    port: int
    weight: int = 1
    status: ServerStatus = ServerStatus.HEALTHY
    active_connections: int = 0
    consecutive_failures: int = 0
    last_health_check: Optional[float] = None


@dataclass
class Request:
    """A simplified request object."""
    request_id: str
    path: str
    data: Any = None


@dataclass
class Response:
    """A simplified response object."""
    status_code: int
    body: Any = None
    server_id: str = ""


@dataclass
class CircuitBreakerConfig:
    """Configuration for the circuit breaker."""
    failure_threshold: int = 5
    cooldown_seconds: float = 30.0
    half_open_max_requests: int = 1


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for a single server."""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[float] = None
    half_open_requests: int = 0


class LoadBalancer:
    """Load balancer with multiple distribution strategies."""

    def __init__(
        self,
        strategy: Strategy = Strategy.ROUND_ROBIN,
        health_check_interval: float = 10.0,
        health_check_timeout: float = 5.0,
    ) -> None:
        self.strategy = strategy
        self.health_check_interval = health_check_interval
        self.health_check_timeout = health_check_timeout
        self.servers: dict[str, Server] = {}
        self._rr_index: int = 0
        self._lock = threading.Lock()
        self._health_checker: Optional[Callable[[Server], bool]] = None
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

    def add_server(self, server: Server) -> None:
        """Register a backend server."""
        self.servers[server.server_id] = server
        self.circuit_breakers[server.server_id] = CircuitBreaker()

    def remove_server(self, server_id: str) -> None:
        """Remove a server from the pool."""
        if server_id in self.servers:
            del self.servers[server_id]
            del self.circuit_breakers[server_id]

    def set_health_checker(self, checker: Callable[[Server], bool]) -> None:
        """Set a custom health check function."""
        self._health_checker = checker

    def get_next_server(self) -> Optional[Server]:
        """Select the next server based on the current strategy."""
        with self._lock:
            if self.strategy == Strategy.ROUND_ROBIN:
                return self._round_robin()
            elif self.strategy == Strategy.WEIGHTED:
                return self._weighted_select()
            elif self.strategy == Strategy.LEAST_CONNECTIONS:
                return self._least_connections()
            return None

    def _round_robin(self) -> Optional[Server]:
        """Round-robin server selection."""
        servers = list(self.servers.values())
        if not servers:
            return None

        # BUG #1: Doesn't check server health status.
        # Should skip unhealthy servers and only return healthy ones.
        server = servers[self._rr_index % len(servers)]
        self._rr_index += 1
        return server

    def _weighted_select(self) -> Optional[Server]:
        """Weighted server selection — higher weight = more traffic."""
        servers = [s for s in self.servers.values() if s.status == ServerStatus.HEALTHY]
        if not servers:
            return None

        # BUG #2: Weight is not properly used. This just picks the server with
        # the highest weight every time instead of distributing proportionally.
        # Should create a weighted distribution where a weight=3 server gets
        # ~3x the requests of a weight=1 server.
        return max(servers, key=lambda s: s.weight)

    def _least_connections(self) -> Optional[Server]:
        """Select server with fewest active connections."""
        # TODO: Implement least-connections strategy
        raise NotImplementedError("Least connections not implemented")

    def handle_request(
        self,
        request: Request,
        handler: Callable[[Server, Request], Response],
    ) -> Response:
        """Route a request to a backend server and handle the response."""
        server = self.get_next_server()
        if server is None:
            return Response(status_code=503, body="No available servers")

        server.active_connections += 1
        try:
            response = handler(server, request)
            response.server_id = server.server_id
            server.consecutive_failures = 0
            return response
        except Exception as e:
            server.consecutive_failures += 1
            return Response(
                status_code=502,
                body=f"Server {server.server_id} error: {e}",
                server_id=server.server_id,
            )
        finally:
            server.active_connections -= 1

    def run_health_checks(self) -> dict[str, bool]:
        """Run health checks on all servers."""
        if not self._health_checker:
            return {}

        results: dict[str, bool] = {}
        for server_id, server in self.servers.items():
            # BUG #3: No timeout enforcement. If the health checker hangs,
            # this hangs too. Should enforce self.health_check_timeout.
            try:
                healthy = self._health_checker(server)
            except Exception:
                healthy = False

            results[server_id] = healthy
            server.status = ServerStatus.HEALTHY if healthy else ServerStatus.UNHEALTHY
            server.last_health_check = time.monotonic()

        return results

    # -------------------------------------------------------------------------
    # TODO: Implement circuit breaker
    # -------------------------------------------------------------------------
    def handle_request_with_circuit_breaker(
        self,
        request: Request,
        handler: Callable[[Server, Request], Response],
        config: CircuitBreakerConfig,
    ) -> Response:
        """Route request with circuit breaker protection per server."""
        raise NotImplementedError("Circuit breaker not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement request draining
    # -------------------------------------------------------------------------
    def drain_server(self, server_id: str, timeout: float = 30.0) -> bool:
        """Gracefully drain a server: stop sending new requests and wait for
        active requests to complete (up to timeout seconds).
        Returns True if all requests completed, False if timeout reached.
        """
        raise NotImplementedError("Request draining not implemented")
