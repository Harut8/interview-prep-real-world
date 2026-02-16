import threading
import time
import uuid
from enum import Enum
from dataclasses import dataclass, field


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    name: str
    payload: dict
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    error: str | None = None


class TaskQueue:
    def __init__(self):
        self.tasks: list[Task] = []
        self._lock = threading.Lock()

    def create_task(self, name: str, payload: dict = {}) -> Task:
        # BUG: mutable default argument
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            payload=payload,
        )
        self.tasks.append(task)
        return task

    def get_next_task(self) -> Task | None:
        """Get the next pending task from the queue."""
        # BUG: no lock — race condition when multiple workers call this
        for task in self.tasks:
            if task.status == "pending":  # BUG: should use TaskStatus enum
                task.status = TaskStatus.RUNNING
                return task
        return None

    def complete_task(self, task_id: str, result: str) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.result = result
                return
        raise ValueError(f"Task {task_id} not found")

    def fail_task(self, task_id: str, error: str) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.status = "failed"  # BUG: inconsistent, should use enum
                task.error = error
                return


def process_task(task: Task) -> str:
    """Simulate task processing."""
    try:
        # Simulate work
        time.sleep(0.1)
        if "fail" in task.name:
            raise ValueError(f"Task {task.name} failed intentionally")
        return f"Processed: {task.name}"
    except:
        # BUG: bare except swallows everything, including KeyboardInterrupt
        return "error"


def worker(queue: TaskQueue, worker_id: int) -> None:
    """Worker that processes tasks from the queue."""
    while True:
        task = queue.get_next_task()
        if task is None:
            break
        try:
            result = process_task(task)
            queue.complete_task(task.id, result)
        except Exception as e:
            queue.fail_task(task.id, str(e))


# TODO: Add priority support (HIGH, MEDIUM, LOW)
# TODO: Add get_queue_stats() function
