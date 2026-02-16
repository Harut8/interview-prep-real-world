# Task 14: User Session Manager — Fix Concurrency Issues & Add Expiration

**Time limit: 60 minutes**

## Existing Codebase
A FastAPI middleware that manages user sessions with in-memory storage. Sessions are created on login and validated on each request.

## Problems to Fix
1. Session IDs are generated with `random.randint` — not cryptographically secure.
2. Sessions never expire — no TTL.
3. The middleware doesn't handle the case where session cookie exists but session was deleted.
4. `get_all_sessions_for_user` iterates over all sessions (O(n)) — needs a secondary index.

## Features to Implement
1. Add session expiration with configurable TTL. Extend session TTL on each access (sliding expiration).
2. Add `DELETE /sessions` endpoint to invalidate all sessions for the current user.
3. Add session metadata: store user agent, IP address, created_at, last_accessed_at.
4. Write tests for session lifecycle.

## What We Evaluate
- Security (session ID generation)
- Data structure design (secondary index)
- Middleware patterns
- Session lifecycle management
