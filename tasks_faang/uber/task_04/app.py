"""
Real-time ETA Service
Estimates time of arrival using a weighted road graph with traffic data.
"""

import heapq
import time
from dataclasses import dataclass, field
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Real-time ETA Service")

CACHE_TTL_SECONDS = 60


@dataclass
class Edge:
    from_node: str
    to_node: str
    base_time_minutes: float  # Base travel time without traffic
    distance_km: float


@dataclass
class RoadGraph:
    """Weighted directed graph representing the road network."""
    adjacency: dict[str, list[Edge]] = field(default_factory=dict)
    nodes: set[str] = field(default_factory=set)

    def add_edge(self, from_node: str, to_node: str,
                 time_minutes: float, distance_km: float):
        self.nodes.add(from_node)
        self.nodes.add(to_node)
        if from_node not in self.adjacency:
            self.adjacency[from_node] = []
        self.adjacency[from_node].append(
            Edge(from_node, to_node, time_minutes, distance_km)
        )

    def get_edges(self, node: str) -> list[Edge]:
        return self.adjacency.get(node, [])


@dataclass
class ETAResult:
    source: str
    destination: str
    total_time_minutes: float
    total_distance_km: float
    path: list[str]
    calculated_at: float = field(default_factory=time.time)


@dataclass
class CacheEntry:
    result: ETAResult
    created_at: float = field(default_factory=time.time)


# --- In-memory storage ---
road_graph = RoadGraph()
traffic_multipliers: dict[tuple[str, str], float] = {}  # (from, to) -> multiplier
eta_cache: dict[tuple[str, str], CacheEntry] = {}


def get_traffic_multiplier(from_node: str, to_node: str) -> float:
    """Get the traffic multiplier for an edge. Default 1.0 (free flow)."""
    return traffic_multipliers.get((from_node, to_node), 1.0)


def get_effective_time(edge: Edge) -> float:
    """
    Get the effective travel time for an edge considering traffic.

    BUG: Traffic multiplier is DIVIDED instead of MULTIPLIED.
    Heavy traffic (multiplier=3.0) should make time 3x longer,
    but currently makes it 3x shorter.
    """
    multiplier = get_traffic_multiplier(edge.from_node, edge.to_node)
    # BUG: Should be multiplication, not division
    return edge.base_time_minutes / multiplier


def dijkstra(graph: RoadGraph, source: str, destination: str) -> Optional[ETAResult]:
    """
    Find shortest path using Dijkstra's algorithm.

    BUG: Does not handle disconnected nodes — when destination is unreachable,
    it fails to return None properly.
    """
    if source not in graph.nodes or destination not in graph.nodes:
        return None

    dist: dict[str, float] = {source: 0.0}
    distance_km: dict[str, float] = {source: 0.0}
    prev: dict[str, Optional[str]] = {source: None}
    heap: list[tuple[float, str]] = [(0.0, source)]
    visited: set[str] = set()

    while heap:
        current_dist, current = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        if current == destination:
            # Reconstruct path
            path = []
            node: Optional[str] = destination
            while node is not None:
                path.append(node)
                node = prev.get(node)
            path.reverse()

            return ETAResult(
                source=source,
                destination=destination,
                total_time_minutes=round(dist[destination], 2),
                total_distance_km=round(distance_km[destination], 2),
                path=path,
            )

        for edge in graph.get_edges(current):
            eff_time = get_effective_time(edge)
            new_dist = current_dist + eff_time

            if edge.to_node not in dist or new_dist < dist[edge.to_node]:
                dist[edge.to_node] = new_dist
                distance_km[edge.to_node] = distance_km[current] + edge.distance_km
                prev[edge.to_node] = current
                heapq.heappush(heap, (new_dist, edge.to_node))

    # BUG: When destination not reached, still tries to return a result
    # instead of returning None
    path = []
    node = destination
    while node is not None:
        path.append(node)
        node = prev.get(node)
    path.reverse()

    return ETAResult(
        source=source,
        destination=destination,
        total_time_minutes=dist.get(destination, 0.0),
        total_distance_km=distance_km.get(destination, 0.0),
        path=path,
    )


def get_cached_eta(source: str, destination: str) -> Optional[ETAResult]:
    """
    Get a cached ETA result if available and not expired.

    BUG: TTL check is inverted — serves stale entries and evicts fresh ones.
    """
    key = (source, destination)
    entry = eta_cache.get(key)
    if entry is None:
        return None

    age = time.time() - entry.created_at
    # BUG: Condition is inverted — should be `age < CACHE_TTL_SECONDS`
    if age > CACHE_TTL_SECONDS:
        return entry.result  # Serves stale data
    else:
        del eta_cache[key]  # Evicts fresh data
        return None


def calculate_eta(source: str, destination: str, use_cache: bool = True) -> Optional[ETAResult]:
    """Calculate ETA between two points, using cache if available."""
    if use_cache:
        cached = get_cached_eta(source, destination)
        if cached is not None:
            return cached

    result = dijkstra(road_graph, source, destination)
    if result is not None:
        eta_cache[(source, destination)] = CacheEntry(result=result)

    return result


# --- API Endpoints ---

class AddEdgeRequest(BaseModel):
    from_node: str
    to_node: str
    time_minutes: float
    distance_km: float


class TrafficUpdate(BaseModel):
    from_node: str
    to_node: str
    multiplier: float


class ETARequest(BaseModel):
    source: str
    destination: str


@app.post("/graph/edges")
def add_edge(data: AddEdgeRequest):
    road_graph.add_edge(data.from_node, data.to_node,
                        data.time_minutes, data.distance_km)
    return {"status": "edge added"}


@app.post("/traffic")
def update_traffic(data: TrafficUpdate):
    traffic_multipliers[(data.from_node, data.to_node)] = data.multiplier
    return {"status": "traffic updated"}


@app.post("/eta")
def get_eta(data: ETARequest):
    result = calculate_eta(data.source, data.destination)
    if result is None:
        raise HTTPException(status_code=404, detail="No route found")
    return {
        "source": result.source,
        "destination": result.destination,
        "total_time_minutes": result.total_time_minutes,
        "total_distance_km": result.total_distance_km,
        "path": result.path,
    }


@app.get("/graph/nodes")
def list_nodes():
    return list(road_graph.nodes)
