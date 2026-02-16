# Task 09: Event System — Fix Observer Pattern & Add Async Support

**Time limit: 60 minutes**

## Existing Codebase
An event emitter / pub-sub system. Supports subscribing handlers to events and emitting events.

## Problems to Fix
1. Unsubscribing during event emission causes `RuntimeError: dictionary changed size during iteration`.
2. Exception in one handler stops all subsequent handlers from being called.
3. The `once` decorator doesn't actually unsubscribe after first call.
4. Handlers are stored by reference — lambda handlers can never be unsubscribed.

## Features to Implement
1. Add async handler support: `async def handler(event)` should work alongside sync handlers.
2. Add event history: `get_history(event_name, limit=10)` returns last N emitted events with timestamps.
3. Write tests for all scenarios.

## What We Evaluate
- Observer pattern correctness
- Async/sync interop
- Error isolation
- Iterator safety
