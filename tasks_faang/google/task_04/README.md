# Task 04: URL Router / API Gateway

**Time Limit: 60 minutes**

## Overview

You are given a URL router that matches HTTP request paths to handler functions,
supporting path parameters (e.g., `/users/{id}`). This is the core routing component
of an API gateway.

## Current State

The router supports registering routes with path parameters, matching incoming
request paths, and extracting parameters. However, there are bugs in matching,
parameter extraction, and route registration.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Greedy route matching** — When multiple routes could match, the router picks
   the first registered route instead of the most specific one. For example,
   `/users/profile` should match the static route `/users/profile` over the
   parameterized route `/users/{id}`.

2. **Path parameter extraction fails with special characters** — Parameters
   containing URL-encoded or special characters (dots, hyphens) are not extracted
   correctly due to an overly restrictive regex pattern.

3. **Duplicate route registration silently overwrites** — Registering the same
   route pattern twice silently replaces the first handler without warning.

## Features to Implement

1. **Middleware Support** — Allow attaching middleware functions to specific routes
   that execute before the handler (for auth, logging, etc.).

2. **Route Groups with Prefixes** — Support grouping routes under a common prefix
   (e.g., all `/api/v1/...` routes share a prefix).

3. **Wildcard Routes** — Support catch-all patterns like `/static/{path:*}` that
   match any remaining path segments.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
