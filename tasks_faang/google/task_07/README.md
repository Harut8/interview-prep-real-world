# Task 07: Load Balancer

**Time Limit: 60 minutes**

## Overview

You are given a load balancer that distributes requests across a pool of backend
servers. It supports round-robin distribution, weighted distribution, and health
checking.

## Current State

The load balancer can register servers, route requests, and perform health checks.
However, there are bugs in the round-robin logic, weighted distribution, and health
check timeout handling.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Round-robin doesn't skip unhealthy servers** — The round-robin algorithm
   sends requests to servers marked as unhealthy, causing failures.

2. **Weighted distribution doesn't account for weight correctly** — The weight
   values are used as-is instead of being normalized, so a server with weight=5
   doesn't actually get 5x the traffic of weight=1.

3. **Health check timeout not enforced** — The health check function doesn't
   actually enforce the configured timeout, potentially hanging indefinitely.

## Features to Implement

1. **Least-Connections Strategy** — Route requests to the server with the fewest
   active connections.

2. **Circuit Breaker** — If a server fails N consecutive requests, open the circuit
   (stop sending requests) for a cooldown period before retrying.

3. **Request Draining** — When removing a server, wait for active requests to
   complete instead of dropping them.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
