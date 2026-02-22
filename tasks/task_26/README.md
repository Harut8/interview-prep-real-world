# Task 26: Event Emitter — Fix Bugs & Add Advanced Features

**Time limit: 60 minutes**

## Existing Codebase
An EventEmitter class (similar to Node.js EventEmitter) that allows registering listeners for named events, emitting events with data, and removing listeners.

## Problems to Fix
1. The `off` method uses list `remove()` which only removes the first occurrence — if a listener is registered twice, only one is removed.
2. The `emit` method doesn't handle listener exceptions — one failing listener prevents subsequent listeners from running.
3. The `once` method doesn't properly remove itself after firing — the wrapper function identity doesn't match for removal.
4. The `listeners` method returns the internal list directly — mutations by the caller corrupt the emitter state.

## Features to Implement
1. Add `once(event, listener)` that works correctly — listener auto-removes after one invocation.
2. Add `prepend_listener(event, listener)` — adds listener to the beginning of the list.
3. Add wildcard support — `on("*", listener)` catches all events.
4. Add `wait_for(event)` — returns an asyncio Future that resolves when the event fires.
5. Add `pipe(target_emitter, events)` — forwards specified events to another emitter.
6. Add max listeners warning — warn when more than N listeners are registered for one event (configurable, default 10).
7. Write tests for all fixed bugs and new features.

## What We Evaluate
- Observer pattern implementation
- Error isolation between listeners
- Async/await integration
- Memory leak prevention
- Test coverage
