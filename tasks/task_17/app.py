import time
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str
    name: str
    func: Callable
    interval: float  # seconds between runs
    status: JobStatus = JobStatus.PENDING
    last_run: float | None = None
    next_run: float | None = None
    error: str | None = None
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)


class Scheduler:
    """Simple background job scheduler."""

    def __init__(self):
        self.jobs: dict[str, Job] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def add_job(
        self,
        func: Callable,
        interval: float,
        name: str = "",
        args: tuple = (),
        kwargs: dict | None = None,
    ) -> str:
        """Add a new job to the scheduler."""
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            id=job_id,
            name=name or func.__name__,
            func=func,
            interval=interval,
            next_run=time.time(),
            args=args,
            kwargs=kwargs or {},
        )
        with self._lock:
            self.jobs[job_id] = job
        return job_id

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        with self._lock:
            if job_id in self.jobs:
                # BUG: just marks as cancelled but doesn't stop if currently running
                self.jobs[job_id].status = JobStatus.CANCELLED
                return True
            return False

    def _run_job(self, job: Job) -> None:
        """Execute a single job."""
        job.status = JobStatus.RUNNING
        job.last_run = time.time()
        try:
            job.func(*job.args, **job.kwargs)
            job.status = JobStatus.COMPLETED
        except Exception as e:
            # BUG: exception here could crash scheduler thread
            job.status = JobStatus.FAILED
            job.error = str(e)
            raise  # This kills the scheduler!

    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            now = time.time()
            with self._lock:
                for job in self.jobs.values():
                    if job.status == JobStatus.CANCELLED:
                        continue
                    if job.next_run and now >= job.next_run:
                        self._run_job(job)
                        # BUG: drift — should calculate next run from scheduled time, not current time
                        job.next_run = time.time() + job.interval

            # BUG: fixed sleep regardless of when next job is due
            time.sleep(0.1)

    def start(self) -> None:
        """Start the scheduler."""
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_jobs(self) -> list[dict]:
        """Return all jobs with their status."""
        with self._lock:
            return [
                {"id": j.id, "name": j.name, "status": j.status.value,
                 "last_run": j.last_run, "next_run": j.next_run}
                for j in self.jobs.values()
            ]


# TODO: Add job dependencies
# TODO: Add max_retries per job
# TODO: Add job history tracking
