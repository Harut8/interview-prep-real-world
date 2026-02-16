# Task 04: Real-time ETA Service

**Time Limit: 60 minutes**

## Overview

You are building Uber's ETA (Estimated Time of Arrival) service. This service uses a weighted graph representing a road network to calculate the shortest travel time between two points. It also incorporates real-time traffic data to adjust estimates.

## Current State

The ETA service has a Dijkstra-based shortest path implementation and a traffic-aware caching layer, but several bugs cause incorrect or broken results.

## Bugs to Fix

1. **Dijkstra Doesn't Handle Disconnected Nodes** - When the source and destination are not connected in the road graph, the algorithm enters an infinite loop or returns an incorrect result instead of indicating "no route found."

2. **Traffic Multiplier Applied Incorrectly** - The traffic multiplier should increase the edge weight (travel time), but it's being applied as a divisor instead of a multiplier. Heavy traffic (multiplier > 1) is making routes appear faster instead of slower.

3. **Cache Invalidation Broken** - ETA results are cached, but the cache TTL check is inverted: it serves stale entries and evicts fresh ones.

## Features to Implement

1. **Multiple Route Options** - Return up to 3 alternative routes (not just the shortest), each with total time and distance. Use a k-shortest-paths approach or penalty method.

2. **Traffic-Aware Pathfinding** - Integrate a traffic data source that provides real-time multipliers per edge. Re-calculate ETAs when traffic data is updated.

## Technical Details

- Road network is a weighted directed graph (adjacency list)
- Edge weights represent travel time in minutes
- Traffic multipliers range from 1.0 (free flow) to 5.0 (severe congestion)
- Cache TTL: 60 seconds

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
