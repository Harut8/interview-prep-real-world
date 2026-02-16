"""Tests for the Load Balancer."""

import time
import threading
import pytest
from app import (
    LoadBalancer,
    Server,
    ServerStatus,
    Strategy,
    Request,
    Response,
    CircuitBreakerConfig,
)


@pytest.fixture
def lb() -> LoadBalancer:
    """Create a load balancer with 3 servers."""
    balancer = LoadBalancer(strategy=Strategy.ROUND_ROBIN)
    balancer.add_server(Server("s1", "10.0.0.1", 8080, weight=1))
    balancer.add_server(Server("s2", "10.0.0.2", 8080, weight=2))
    balancer.add_server(Server("s3", "10.0.0.3", 8080, weight=3))
    return balancer


def success_handler(server: Server, request: Request) -> Response:
    """A handler that always succeeds."""
    return Response(status_code=200, body=f"OK from {server.server_id}")


def fail_handler(server: Server, request: Request) -> Response:
    """A handler that always raises an exception."""
    raise RuntimeError("Server error")


class TestRoundRobin:
    """Tests for round-robin — FAILING due to Bug #1."""

    def test_basic_round_robin(self, lb: LoadBalancer) -> None:
        """Requests should cycle through servers."""
        servers_used = []
        for i in range(6):
            server = lb.get_next_server()
            servers_used.append(server.server_id)

        # Should cycle: s1, s2, s3, s1, s2, s3
        assert servers_used == ["s1", "s2", "s3", "s1", "s2", "s3"]

    def test_round_robin_skips_unhealthy(self, lb: LoadBalancer) -> None:
        """Round-robin should skip unhealthy servers.
        FAILING: Bug #1 — unhealthy servers are not skipped.
        """
        lb.servers["s2"].status = ServerStatus.UNHEALTHY

        servers_used = []
        for _ in range(4):
            server = lb.get_next_server()
            servers_used.append(server.server_id)

        assert "s2" not in servers_used, (
            f"Unhealthy server s2 was selected. Servers used: {servers_used}. "
            f"Round-robin should skip unhealthy servers."
        )

    def test_all_unhealthy_returns_none(self, lb: LoadBalancer) -> None:
        """If all servers are unhealthy, should return None."""
        for s in lb.servers.values():
            s.status = ServerStatus.UNHEALTHY

        server = lb.get_next_server()
        # With bug #1 fixed, this should return None
        # Currently it returns an unhealthy server


class TestWeightedDistribution:
    """Tests for weighted distribution — FAILING due to Bug #2."""

    def test_weighted_proportional(self) -> None:
        """Servers should receive traffic proportional to their weights.
        FAILING: Bug #2 — always picks the highest-weight server.
        """
        lb = LoadBalancer(strategy=Strategy.WEIGHTED)
        lb.add_server(Server("light", "10.0.0.1", 8080, weight=1))
        lb.add_server(Server("heavy", "10.0.0.2", 8080, weight=3))

        counts: dict[str, int] = {"light": 0, "heavy": 0}
        for i in range(400):
            server = lb.get_next_server()
            if server:
                counts[server.server_id] += 1

        # heavy should get ~3x light's traffic, but not ALL traffic
        assert counts["light"] > 50, (
            f"Light server got only {counts['light']} requests out of 400. "
            f"Weight=1 should still get ~25% (100) requests."
        )
        assert counts["heavy"] > counts["light"]


class TestHealthChecks:
    """Tests for health checking — FAILING due to Bug #3."""

    def test_basic_health_check(self, lb: LoadBalancer) -> None:
        """Health check should update server status."""
        lb.set_health_checker(lambda s: s.server_id != "s2")
        results = lb.run_health_checks()

        assert results["s1"] is True
        assert results["s2"] is False
        assert lb.servers["s2"].status == ServerStatus.UNHEALTHY

    def test_health_check_timeout(self, lb: LoadBalancer) -> None:
        """Health check should time out if checker takes too long.
        FAILING: Bug #3 — no timeout enforcement on health checker.
        """
        lb.health_check_timeout = 0.5

        def slow_checker(server: Server) -> bool:
            time.sleep(2.0)  # Takes 2 seconds, timeout is 0.5
            return True

        lb.set_health_checker(slow_checker)

        start = time.monotonic()
        results = lb.run_health_checks()
        elapsed = time.monotonic() - start

        # Should complete in ~0.5s per server (with timeout), not 2s per server
        assert elapsed < 3.0, (
            f"Health checks took {elapsed:.1f}s. With 0.5s timeout and 3 servers, "
            f"should take at most ~1.5s. Timeout is not being enforced."
        )


class TestRequestHandling:
    """Tests for request handling."""

    def test_successful_request(self, lb: LoadBalancer) -> None:
        """Successful request should return 200."""
        req = Request(request_id="r1", path="/api/test")
        resp = lb.handle_request(req, success_handler)
        assert resp.status_code == 200

    def test_server_error_tracked(self, lb: LoadBalancer) -> None:
        """Failed request should increment consecutive_failures."""
        req = Request(request_id="r1", path="/api/test")
        resp = lb.handle_request(req, fail_handler)
        assert resp.status_code == 502


class TestLeastConnections:
    """Tests for least-connections strategy — TODO: implement."""

    def test_least_connections_selection(self) -> None:
        """TODO: Should select the server with fewest active connections."""
        lb = LoadBalancer(strategy=Strategy.LEAST_CONNECTIONS)
        lb.add_server(Server("s1", "10.0.0.1", 8080, active_connections=5))
        lb.add_server(Server("s2", "10.0.0.2", 8080, active_connections=2))
        lb.add_server(Server("s3", "10.0.0.3", 8080, active_connections=8))

        server = lb.get_next_server()
        assert server.server_id == "s2"


class TestCircuitBreaker:
    """Tests for circuit breaker — TODO: implement."""

    def test_circuit_opens_after_failures(self) -> None:
        """TODO: After N consecutive failures, circuit should open."""
        lb = LoadBalancer()
        lb.add_server(Server("s1", "10.0.0.1", 8080))
        config = CircuitBreakerConfig(failure_threshold=3, cooldown_seconds=1.0)

        for i in range(3):
            req = Request(request_id=f"r{i}", path="/api/test")
            lb.handle_request_with_circuit_breaker(req, fail_handler, config)

        # After 3 failures, circuit should be open
        req = Request(request_id="r4", path="/api/test")
        resp = lb.handle_request_with_circuit_breaker(req, success_handler, config)
        assert resp.status_code == 503  # Service unavailable due to open circuit


class TestDraining:
    """Tests for request draining — TODO: implement."""

    def test_drain_waits_for_active(self, lb: LoadBalancer) -> None:
        """TODO: Drain should wait for active requests to finish."""
        lb.servers["s1"].active_connections = 2
        lb.servers["s1"].status = ServerStatus.HEALTHY

        result = lb.drain_server("s1", timeout=5.0)
        assert lb.servers.get("s1") is None or lb.servers["s1"].status == ServerStatus.DRAINING
