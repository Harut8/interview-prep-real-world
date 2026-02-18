1. Drift fix — `next_run` calculation (line 96)
    - current: `job.next_run = time.time() + job.interval` — drifts because it uses current time
    - fix: `job.next_run = job.next_run + job.interval` — anchored to scheduled time
    - e.g. scheduled at t=10, ran at t=10.05 → next should be t=13, not t=13.05
    - `next_run = time.time()` on line 55 is fine — runs immediately on first tick (intentional)
    - DI for clock (`clock=time.time` in `__init__`) for testability

2. Cancel running job (line 67-68)
    - can't force-kill a thread in Python
    - use `threading.Event` for cooperative cancellation — job checks event periodically
    - `join(timeout)` to wait for job to finish

3. Exception kills scheduler (line 83) — remove `raise`
    - `raise` propagates out of `_run_job` into `_scheduler_loop`, crashes the thread
    - already marked as FAILED and error stored — just remove the `raise`

4. Sleep drift (line 99) — compute next due time instead of fixed 0.1s
    - calculate time until nearest `next_run`:
        ```
        next_due = min(j.next_run for j in jobs if j.next_run and j.status != CANCELLED)
        sleep_time = max(0, next_due - time.time())
        ```
    - better: use `threading.Event.wait(timeout=sleep_time)` instead of `time.sleep`
      so `stop()` can wake it immediately

5. Job overlap / pileup
    - current code runs `_run_job` synchronously inside the lock → no actual overlap possible
    - but this means all jobs run sequentially, blocking the scheduler
    - real fix: run jobs in separate threads (or thread pool), then skip if `status == RUNNING`:
        ```
        if job.status in (JobStatus.CANCELLED, JobStatus.RUNNING):
            continue
        ```
    - COMPLETED jobs should NOT be skipped — they're recurring (COMPLETED → RUNNING → COMPLETED)

6. Lock held during job execution (lines 89-96) — biggest issue
    - `_run_job` is called inside `with self._lock` — lock held for entire job duration
    - no other jobs can be added/cancelled while a job runs
    - fix: collect jobs due to run inside the lock, release lock, then run them outside:
        ```
        with self._lock:
            due_jobs = [j for j in self.jobs.values() if j.next_run and now >= j.next_run and ...]
        for job in due_jobs:
            self._run_job(job)  # outside lock
        ```
    - or better: submit to a thread pool

7. `_running` flag not thread-safe (lines 87, 103, 109)
    - bool read in scheduler thread, written from main thread without synchronization
    - fix: use `threading.Event` instead:
        ```
        self._stop_event = threading.Event()
        # loop: while not self._stop_event.is_set()
        # stop: self._stop_event.set()
        ```

8. Max retries per job
    - add `max_retries` and `retry_count` to Job dataclass
    - on failure: if `retry_count < max_retries`, increment count, reschedule with backoff
    - jobs must be idempotent for retries to be safe

9. Job dependencies — graph with cycle detection
    - store `depends_on: list[str]` per job
    - before running: check all dependencies completed successfully
    - detect circular dependencies with topological sort or DFS when adding dependencies
    - design decision: if dependency fails, should dependent job be blocked/failed/skipped?

10. History — bounded list of last N runs
    - `_history: dict[str, list]` — job_id → list of run records
    - each record: `{status, start_time, end_time, duration, error}`
    - cap at N entries per job (e.g. 100), drop oldest

11. Tests to write
    - failing job doesn't crash scheduler (other jobs still run)
    - drift: with mock clock, verify `next_run` is anchored to schedule, not wall time
    - overlap: long-running job skipped on next tick if still running
    - cancel: cancelled job doesn't run on next tick
    - dependencies: Job B runs only after Job A completes successfully
    - dependencies: circular dependency detected and rejected
    - dependencies: Job B blocked when Job A fails
    - max retries: failed job retried N times then marked permanently failed
    - history: returns last N runs with correct status/duration
    - concurrent: add/cancel jobs while scheduler is running