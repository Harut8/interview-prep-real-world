1. Exception isolation in `emit` (line 34-35)
    - wrap each handler call in try/except, continue on exception
    - log or collect errors but don't stop other handlers

2. Iteration safety — fix is in `emit`, NOT in `off`
    - `off()` itself is fine — it just does `list.remove()`
    - the bug is in `emit` (line 33): iterates `self._handlers[event]` directly
    - if a handler calls `off()` during iteration, list mutates mid-loop → RuntimeError
    - fix: iterate over a **copy** in `emit`:
        `for handler in list(self._handlers[event]):`

3. `once` bug (line 25) — `self.off(event, handler)` should be `self.off(event, wrapper)`
    - `handler` was never registered, `wrapper` was
    - so `off` can't find `handler` in the list, nothing gets removed
    - the handler keeps firing on every emit

4. Lambda unsubscribe problem
    - `off()` uses `list.remove()` which compares by identity
    - two identical lambdas are different objects, so `off` can never find them
    - fix: `on()` should return a subscription ID/handle, `off()` accepts that ID
    - or store handlers as `{id: handler}` dict instead of a list

5. Async support — separate `emit_async` method, not "make all funcs async"
    - can't just make `emit` async — sync callers would need `await` everywhere
    - add `async def emit_async(self, event, *args, **kwargs):`
    - inside: check `asyncio.iscoroutinefunction(handler)` for each handler
        - if async: `await handler(*args, **kwargs)`
        - if sync: `handler(*args, **kwargs)`
    - keep original `emit` for pure sync usage

6. History tracking — `_history` on `EventEmitter`, not "Event class"
    - `_history: dict[str, list[tuple[float, Any]]]` — event name → list of (timestamp, args)
    - in `emit`: append `(time.time(), args, kwargs)` to `_history[event]`
    - `get_history(event_name, limit=10)` returns last N entries
    - DI for clock (same pattern as previous tasks) for testability

7. `listeners()` (line 38-39) — returns the internal list directly
    - callers can mutate it from outside, breaking encapsulation
    - fix: return a copy: `return list(self._handlers.get(event, []))`

8. `remove_all` bug (line 43) — `if event:` is falsy for empty string `""`
    - should be `if event is not None:` to correctly handle edge case

9. Tests to write
    - exception in handler doesn't stop others
    - unsubscribe during emit doesn't crash, remaining handlers still fire
    - `once` handler fires exactly once across multiple emits
    - lambda can be unsubscribed via returned ID/handle
    - async handler runs correctly alongside sync handlers
    - history: returns correct events, respects limit, includes timestamps
    - `remove_all(None)` clears everything, `remove_all("")` only clears "" event
    - `listeners()` returns a copy (mutating it doesn't affect emitter)