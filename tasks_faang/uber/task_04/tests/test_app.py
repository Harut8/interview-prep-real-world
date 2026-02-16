"""
Tests for Real-time ETA Service.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import time
from app import (
    RoadGraph,
    Edge,
    ETAResult,
    CacheEntry,
    road_graph,
    traffic_multipliers,
    eta_cache,
    dijkstra,
    get_effective_time,
    get_cached_eta,
    calculate_eta,
    CACHE_TTL_SECONDS,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all state before each test."""
    road_graph.adjacency.clear()
    road_graph.nodes.clear()
    traffic_multipliers.clear()
    eta_cache.clear()
    yield
    road_graph.adjacency.clear()
    road_graph.nodes.clear()
    traffic_multipliers.clear()
    eta_cache.clear()


def _build_simple_graph():
    """Build a simple graph: A -> B -> C -> D, with A -> C shortcut."""
    road_graph.add_edge("A", "B", 5.0, 3.0)
    road_graph.add_edge("B", "C", 3.0, 2.0)
    road_graph.add_edge("C", "D", 4.0, 3.0)
    road_graph.add_edge("A", "C", 10.0, 6.0)  # Longer shortcut


class TestDijkstra:
    def test_shortest_path_simple(self):
        """This test should PASS — finds shortest path A->B->C->D."""
        _build_simple_graph()
        result = dijkstra(road_graph, "A", "D")
        assert result is not None
        assert result.path == ["A", "B", "C", "D"]
        assert result.total_time_minutes == pytest.approx(12.0)

    def test_direct_neighbor(self):
        """This test should PASS — direct edge A->B."""
        _build_simple_graph()
        result = dijkstra(road_graph, "A", "B")
        assert result is not None
        assert result.path == ["A", "B"]
        assert result.total_time_minutes == pytest.approx(5.0)

    def test_disconnected_nodes_returns_none(self):
        """
        FAILING: When destination is unreachable, should return None.
        Currently returns a bogus ETAResult.
        """
        _build_simple_graph()
        road_graph.add_edge("X", "Y", 2.0, 1.0)  # Disconnected component

        result = dijkstra(road_graph, "A", "Y")
        assert result is None, "Should return None for unreachable destination"

    def test_unknown_node_returns_none(self):
        """This test should PASS — unknown source/dest returns None."""
        _build_simple_graph()
        result = dijkstra(road_graph, "A", "UNKNOWN")
        assert result is None


class TestTraffic:
    def test_effective_time_with_traffic(self):
        """
        FAILING: Traffic multiplier of 2.0 should DOUBLE the time.
        Bug: it divides instead (time becomes half).
        """
        edge = Edge("A", "B", 10.0, 5.0)
        traffic_multipliers[("A", "B")] = 2.0
        eff = get_effective_time(edge)
        assert eff == pytest.approx(20.0), (
            f"Expected 20.0 but got {eff} — multiplier divides instead of multiplying"
        )

    def test_no_traffic_uses_base_time(self):
        """This test should PASS — no traffic means base time."""
        edge = Edge("A", "B", 10.0, 5.0)
        eff = get_effective_time(edge)
        assert eff == pytest.approx(10.0)


class TestCache:
    def test_cache_serves_fresh_entry(self):
        """
        FAILING: Fresh cache entries should be served,
        but the inverted TTL check evicts them.
        """
        result = ETAResult("A", "B", 5.0, 3.0, ["A", "B"])
        eta_cache[("A", "B")] = CacheEntry(result=result, created_at=time.time())

        cached = get_cached_eta("A", "B")
        assert cached is not None, "Fresh cache entry should be served"
        assert cached.source == "A"

    def test_cache_miss_returns_none(self):
        """This test should PASS — no cache entry returns None."""
        cached = get_cached_eta("A", "B")
        assert cached is None


class TestMultipleRoutes:
    # TODO: Implement k-shortest paths
    # def test_returns_up_to_3_routes(self):
    #     """Should return up to 3 alternative routes."""
    #     pass

    # TODO: Alternative routes are distinct
    # def test_alternative_routes_differ(self):
    #     """Returned routes should have meaningfully different paths."""
    #     pass
    pass


class TestTrafficAwarePathfinding:
    # TODO: Integrate real-time traffic into pathfinding
    # def test_eta_changes_with_traffic_update(self):
    #     """After traffic update, recalculated ETA should reflect new conditions."""
    #     pass

    # TODO: Heavy traffic rerouting
    # def test_heavy_traffic_causes_reroute(self):
    #     """When one path has heavy traffic, shortest path should change."""
    #     pass
    pass
