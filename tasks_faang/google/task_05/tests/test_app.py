"""Tests for the Task DAG Executor."""

import time
from typing import Any

import pytest
from app import DAGExecutor, TaskDef, TaskStatus, DAGExecutionResult


def make_task(value: Any = None, delay: float = 0.0):
    """Create a simple task function that returns a value."""
    def func(context: dict) -> Any:
        if delay:
            time.sleep(delay)
        return value
    return func


class TestDAGValidation:
    """Tests for DAG validation — FAILING due to Bug #1."""

    def test_self_loop_detected(self) -> None:
        """Direct self-loop should be detected."""
        executor = DAGExecutor()
        executor.add_task(TaskDef("a", make_task(), dependencies=["a"]))
        errors = executor.validate_dag()
        assert len(errors) > 0

    def test_indirect_cycle_detected(self) -> None:
        """Indirect cycle A -> B -> C -> A should be detected.
        FAILING: Bug #1 — only direct self-loops are caught.
        """
        executor = DAGExecutor()
        executor.add_task(TaskDef("a", make_task(), dependencies=["c"]))
        executor.add_task(TaskDef("b", make_task(), dependencies=["a"]))
        executor.add_task(TaskDef("c", make_task(), dependencies=["b"]))
        errors = executor.validate_dag()
        assert any("cycle" in e.lower() for e in errors), (
            f"Cycle A->B->C->A not detected. Errors: {errors}"
        )

    def test_missing_dependency_detected(self) -> None:
        """Reference to non-existent task should be an error."""
        executor = DAGExecutor()
        executor.add_task(TaskDef("a", make_task(), dependencies=["nonexistent"]))
        errors = executor.validate_dag()
        assert len(errors) > 0


class TestBasicExecution:
    """Tests for basic execution — some fail due to bugs."""

    def test_simple_linear_dag(self) -> None:
        """A -> B -> C should execute in order."""
        executor = DAGExecutor()
        execution_order: list[str] = []

        def make_ordered_task(name: str):
            def func(ctx):
                execution_order.append(name)
                return name
            return func

        executor.add_task(TaskDef("a", make_ordered_task("a")))
        executor.add_task(TaskDef("b", make_ordered_task("b"), dependencies=["a"]))
        executor.add_task(TaskDef("c", make_ordered_task("c"), dependencies=["b"]))

        result = executor.execute()
        assert result.success
        assert execution_order == ["a", "b", "c"]

    def test_results_passed_to_dependents(self) -> None:
        """Task results should be available to downstream tasks in context.
        FAILING: Bug #2 — results not written to context dict.
        """
        executor = DAGExecutor()

        def producer(ctx: dict) -> int:
            return 42

        def consumer(ctx: dict) -> int:
            return ctx["producer"] * 2

        executor.add_task(TaskDef("producer", producer))
        executor.add_task(TaskDef("consumer", consumer, dependencies=["producer"]))

        result = executor.execute()
        assert result.success, f"Execution failed: {result.task_results}"
        assert result.task_results["consumer"].result == 84, (
            "Consumer should see producer's result (42) in context and return 84."
        )

    def test_independent_tasks_run(self) -> None:
        """Independent tasks should all complete."""
        executor = DAGExecutor(max_workers=2)

        executor.add_task(TaskDef("a", make_task("a")))
        executor.add_task(TaskDef("b", make_task("b")))
        executor.add_task(TaskDef("c", make_task("c")))

        result = executor.execute()
        assert result.success
        assert len(result.task_results) == 3


class TestParallelism:
    """Tests for parallelism control — FAILING due to Bug #3."""

    def test_max_workers_respected(self) -> None:
        """Should not run more tasks concurrently than max_workers.
        FAILING: Bug #3 — ThreadPoolExecutor created without max_workers arg.
        """
        executor = DAGExecutor(max_workers=2)
        max_concurrent = {"value": 0}
        current_concurrent = {"value": 0}
        lock = __import__("threading").Lock()

        def counting_task(ctx: dict) -> str:
            with lock:
                current_concurrent["value"] += 1
                max_concurrent["value"] = max(
                    max_concurrent["value"], current_concurrent["value"]
                )
            time.sleep(0.1)
            with lock:
                current_concurrent["value"] -= 1
            return "done"

        # Add 4 independent tasks
        for i in range(4):
            executor.add_task(TaskDef(f"task_{i}", counting_task))

        result = executor.execute()
        assert result.success
        assert max_concurrent["value"] <= 2, (
            f"Max concurrent tasks was {max_concurrent['value']}, "
            f"but max_workers=2. Parallelism not respected."
        )


class TestFailureHandling:
    """Tests for task failure propagation."""

    def test_failed_task_skips_dependents(self) -> None:
        """If task A fails, dependent task B should be skipped."""
        executor = DAGExecutor()

        def failing_task(ctx):
            raise RuntimeError("boom")

        executor.add_task(TaskDef("a", failing_task))
        executor.add_task(TaskDef("b", make_task("b"), dependencies=["a"]))

        result = executor.execute()
        assert not result.success
        assert result.task_results["a"].status == TaskStatus.FAILED
        assert result.task_results["b"].status == TaskStatus.SKIPPED


class TestRetry:
    """Tests for retry with backoff — TODO: implement."""

    def test_retry_on_failure(self) -> None:
        """TODO: Task should retry up to max_retries times."""
        executor = DAGExecutor()
        attempt = {"count": 0}

        def flaky(ctx):
            attempt["count"] += 1
            if attempt["count"] < 3:
                raise RuntimeError("transient error")
            return "success"

        executor.add_task(TaskDef("flaky", flaky, max_retries=3))
        result = executor.execute()
        assert result.success
        assert result.task_results["flaky"].retries == 2


class TestTimeline:
    """Tests for timeline visualization — TODO: implement."""

    def test_timeline_output(self) -> None:
        """TODO: Timeline should show task execution periods."""
        executor = DAGExecutor()
        executor.add_task(TaskDef("a", make_task("a", delay=0.05)))
        executor.add_task(TaskDef("b", make_task("b", delay=0.05), dependencies=["a"]))
        executor.execute()

        timeline = executor.get_timeline()
        assert "a" in timeline
        assert "b" in timeline
