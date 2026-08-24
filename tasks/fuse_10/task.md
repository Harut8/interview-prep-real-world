# Task Scheduler / Job Queue with Retries

**Practical LLD — maps to Fuse's "system design with error handling" style.**

Implement a job queue that executes tasks with priorities, retries on failure, and tracks status.

## Interface

```python
class JobQueue:
    def __init__(self, max_workers: int = 1) -> None: ...
    def submit(self, job_id: str, fn: Callable, priority: int = 0, max_retries: int = 0) -> None: ...
    def get_status(self, job_id: str) -> str: ...
    def get_result(self, job_id: str) -> Any: ...
    def cancel(self, job_id: str) -> bool: ...
    def drain(self) -> None: ...
```

## Requirements

- `submit(job_id, fn, priority, max_retries)` — enqueues a job. Higher `priority` runs first.
- Jobs transition through states: `pending` → `running` → `completed` | `failed` | `cancelled`.
- On failure (fn raises), retry up to `max_retries` times with exponential backoff.
- `get_status(job_id)` returns the current state string.
- `get_result(job_id)` returns the return value if completed, or raises if failed/pending.
- `cancel(job_id)` cancels a pending job (cannot cancel running).
- `drain()` blocks until all pending/running jobs complete.
- Thread-safe.

## Patterns Tested

Priority queue, state machine, thread pool, retry logic, concurrent data structures.

## Time Target: 50 minutes
