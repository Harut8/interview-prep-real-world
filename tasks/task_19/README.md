# Task 19: Database Connection Pool — Fix Resource Management & Add Health Checks

**Time limit: 60 minutes**

## Existing Codebase
A connection pool manager for database connections. Manages a pool of reusable connections with configurable pool size.

## Problems to Fix
1. Connections are never returned to the pool after use (resource leak).
2. No timeout when waiting for an available connection — can deadlock.
3. The pool doesn't validate connections before handing them out (connection may be stale).
4. `close_all()` doesn't wait for in-use connections to be returned.

## Features to Implement
1. Add connection health check: `ping()` before handing out a connection. Remove dead connections.
2. Add pool statistics: `get_stats()` returning total, available, in_use, created, errors counts.
3. Add context manager support: `with pool.connection() as conn: ...`
4. Write tests for pool behavior under concurrent load.

## What We Evaluate
- Resource management patterns
- Context managers
- Threading / synchronization
- Connection lifecycle
