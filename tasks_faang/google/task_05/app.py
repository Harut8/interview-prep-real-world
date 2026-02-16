"""
Task DAG Executor

Execute a DAG of dependent tasks with parallel execution, respecting dependencies
and controlling concurrency.
"""

from __future__ import annotations

import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskDef:
    """Definition of a task in the DAG."""
    task_id: str
    func: Callable[[dict[str, Any]], Any]
    dependencies: list[str] = field(default_factory=list)
    max_retries: int = 0
    condition: Optional[Callable[[dict[str, Any]], bool]] = None


@dataclass
class TaskResult:
    """Result of executing a task."""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    retries: int = 0


@dataclass
class DAGExecutionResult:
    """Overall result of executing a DAG."""
    task_results: dict[str, TaskResult] = field(default_factory=dict)
    success: bool = True
    execution_time: float = 0.0


class DAGExecutor:
    """Executes a DAG of tasks with dependency resolution and parallelism."""

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers
        self.tasks: dict[str, TaskDef] = {}
        self.results: dict[str, TaskResult] = {}
        self._lock = threading.Lock()

    def add_task(self, task: TaskDef) -> None:
        """Add a task to the DAG."""
        self.tasks[task.task_id] = task

    def validate_dag(self) -> list[str]:
        """Validate the DAG and return list of errors."""
        errors: list[str] = []

        # Check for missing dependencies
        for task_id, task in self.tasks.items():
            for dep in task.dependencies:
                if dep not in self.tasks:
                    errors.append(f"Task '{task_id}' depends on unknown task '{dep}'")

        # BUG #1: Only checks direct self-loops, misses longer cycles.
        # e.g., A -> B -> C -> A would not be detected.
        for task_id, task in self.tasks.items():
            if task_id in task.dependencies:
                errors.append(f"Task '{task_id}' has a self-dependency cycle")

        return errors

    def execute(self) -> DAGExecutionResult:
        """Execute all tasks in the DAG respecting dependencies."""
        errors = self.validate_dag()
        if errors:
            dag_result = DAGExecutionResult(success=False)
            return dag_result

        start_time = time.monotonic()
        self.results.clear()
        completed: set[str] = set()
        failed: set[str] = set()
        context: dict[str, Any] = {}  # Shared results context

        # BUG #3: Creates executor with unlimited workers, ignoring max_workers.
        # All ready tasks get submitted at once instead of respecting the limit.
        with ThreadPoolExecutor() as executor:
            pending_futures: dict[str, Future] = {}

            while len(completed) + len(failed) < len(self.tasks):
                # Find tasks that are ready to run
                ready = []
                for task_id, task in self.tasks.items():
                    if task_id in completed or task_id in failed:
                        continue
                    if task_id in pending_futures:
                        continue
                    if all(dep in completed for dep in task.dependencies):
                        ready.append(task)

                # Submit all ready tasks
                for task in ready:
                    future = executor.submit(self._execute_task, task, context)
                    pending_futures[task.task_id] = future

                # Wait for any task to complete
                if pending_futures:
                    done_ids = []
                    for task_id, future in pending_futures.items():
                        if future.done():
                            done_ids.append(task_id)
                            task_result = future.result()
                            self.results[task_id] = task_result

                            if task_result.status == TaskStatus.COMPLETED:
                                completed.add(task_id)
                                # BUG #2: Result is NOT put into context here.
                                # Downstream tasks won't see the result.
                                # Missing: context[task_id] = task_result.result
                            else:
                                failed.add(task_id)
                                # Also mark dependents as failed
                                self._mark_dependents_failed(task_id, failed)

                    for task_id in done_ids:
                        del pending_futures[task_id]

                if not pending_futures and not ready:
                    # Deadlock — remaining tasks have unresolvable deps
                    break

                time.sleep(0.01)  # Avoid busy-waiting

        execution_time = time.monotonic() - start_time
        return DAGExecutionResult(
            task_results=self.results,
            success=len(failed) == 0,
            execution_time=execution_time,
        )

    def _execute_task(self, task: TaskDef, context: dict[str, Any]) -> TaskResult:
        """Execute a single task."""
        result = TaskResult(task_id=task.task_id, status=TaskStatus.RUNNING)
        result.start_time = time.monotonic()

        try:
            output = task.func(context)
            result.result = output
            result.status = TaskStatus.COMPLETED
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)

        result.end_time = time.monotonic()
        return result

    def _mark_dependents_failed(self, failed_task_id: str, failed: set[str]) -> None:
        """Recursively mark tasks that depend on a failed task."""
        for task_id, task in self.tasks.items():
            if task_id in failed:
                continue
            if failed_task_id in task.dependencies:
                failed.add(task_id)
                self.results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.SKIPPED,
                    error=f"Dependency '{failed_task_id}' failed",
                )
                self._mark_dependents_failed(task_id, failed)

    # -------------------------------------------------------------------------
    # TODO: Implement retry with exponential backoff
    # -------------------------------------------------------------------------
    def _execute_with_retry(
        self, task: TaskDef, context: dict[str, Any]
    ) -> TaskResult:
        """Execute a task with retry logic and exponential backoff."""
        raise NotImplementedError("Retry with backoff not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement execution timeline visualization
    # -------------------------------------------------------------------------
    def get_timeline(self) -> str:
        """Generate a text-based Gantt chart of the execution.
        Example output:
            task_a: |====|
            task_b:      |========|
            task_c:      |====|
            task_d:                |====|
        """
        raise NotImplementedError("Timeline visualization not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement conditional task execution
    # -------------------------------------------------------------------------
    def _should_execute(self, task: TaskDef, context: dict[str, Any]) -> bool:
        """Check if a conditional task should execute based on upstream results."""
        raise NotImplementedError("Conditional execution not implemented")
