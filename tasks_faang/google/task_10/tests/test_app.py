"""Tests for the Data Pipeline Orchestrator."""

from typing import Any
from collections import defaultdict

import pytest
from app import (
    PipelineOrchestrator,
    PipelineDefinition,
    Stage,
    StageStatus,
    CronSchedule,
)


def make_stage_func(output: Any = None, delay: float = 0.0):
    """Create a simple stage function."""
    def func(context: dict) -> Any:
        if delay:
            import time
            time.sleep(delay)
        return output
    return func


def make_failing_func(error_msg: str = "stage failed"):
    def func(context: dict) -> Any:
        raise RuntimeError(error_msg)
    return func


@pytest.fixture
def orchestrator() -> PipelineOrchestrator:
    return PipelineOrchestrator()


@pytest.fixture
def simple_pipeline() -> PipelineDefinition:
    """A -> B -> C linear pipeline."""
    return PipelineDefinition(
        pipeline_id="simple",
        name="Simple Pipeline",
        stages=[
            Stage("extract", "Extract", make_stage_func(output={"rows": 100})),
            Stage("transform", "Transform", make_stage_func(output={"rows": 95}), dependencies=["extract"]),
            Stage("load", "Load", make_stage_func(output={"loaded": 95}), dependencies=["transform"]),
        ],
    )


@pytest.fixture
def diamond_pipeline() -> PipelineDefinition:
    """Diamond: extract -> (clean, validate) -> merge."""
    return PipelineDefinition(
        pipeline_id="diamond",
        name="Diamond Pipeline",
        stages=[
            Stage("extract", "Extract", make_stage_func(output="raw_data")),
            Stage("clean", "Clean", make_stage_func(output="clean_data"), dependencies=["extract"]),
            Stage("validate", "Validate", make_stage_func(output="valid_data"), dependencies=["extract"]),
            Stage("merge", "Merge", make_stage_func(output="merged"), dependencies=["clean", "validate"]),
        ],
    )


class TestBasicExecution:
    """Tests for basic pipeline execution."""

    def test_linear_pipeline(self, orchestrator: PipelineOrchestrator, simple_pipeline: PipelineDefinition) -> None:
        """Linear pipeline should execute all stages in order."""
        orchestrator.register_pipeline(simple_pipeline)
        run = orchestrator.execute("simple")

        assert run.status == StageStatus.COMPLETED
        assert len(run.stage_results) == 3
        assert all(r.status == StageStatus.COMPLETED for r in run.stage_results.values())

    def test_stage_output_in_context(self, orchestrator: PipelineOrchestrator, simple_pipeline: PipelineDefinition) -> None:
        """Each stage should be able to see previous stage outputs in context."""
        call_log: list[str] = []

        def transform_with_check(ctx: dict) -> dict:
            call_log.append("transform")
            assert "extract" in ctx, "Extract output should be in context"
            return {"rows": ctx["extract"]["rows"] - 5}

        simple_pipeline.stages[1] = Stage(
            "transform", "Transform", transform_with_check, dependencies=["extract"]
        )
        orchestrator.register_pipeline(simple_pipeline)
        run = orchestrator.execute("simple")
        assert "transform" in call_log


class TestDiamondDependency:
    """Tests for diamond dependency — FAILING due to Bug #1."""

    def test_diamond_no_duplicate_execution(self, orchestrator: PipelineOrchestrator, diamond_pipeline: PipelineDefinition) -> None:
        """In diamond pattern, shared upstream should execute exactly once.
        FAILING: Bug #1 — extract stage runs twice.
        """
        execution_count: dict[str, int] = defaultdict(int)

        def counting_func(stage_name: str):
            def func(ctx: dict) -> str:
                execution_count[stage_name] += 1
                return f"{stage_name}_output"
            return func

        diamond_pipeline.stages = [
            Stage("extract", "Extract", counting_func("extract")),
            Stage("clean", "Clean", counting_func("clean"), dependencies=["extract"]),
            Stage("validate", "Validate", counting_func("validate"), dependencies=["extract"]),
            Stage("merge", "Merge", counting_func("merge"), dependencies=["clean", "validate"]),
        ]

        orchestrator.register_pipeline(diamond_pipeline)
        run = orchestrator.execute("diamond")

        assert execution_count["extract"] == 1, (
            f"'extract' executed {execution_count['extract']} times, expected 1. "
            f"Diamond dependency causes duplicate execution."
        )
        assert run.status == StageStatus.COMPLETED


class TestErrorPropagation:
    """Tests for error propagation — FAILING due to Bug #2."""

    def test_failure_skips_dependents(self, orchestrator: PipelineOrchestrator) -> None:
        """If a stage fails, dependent stages should not execute.
        FAILING: Bug #2 — dependents execute regardless of upstream failure.
        """
        executed: list[str] = []

        def track_and_fail(ctx: dict) -> Any:
            executed.append("transform")
            raise RuntimeError("Transform failed")

        def track_load(ctx: dict) -> Any:
            executed.append("load")
            return "loaded"

        pipeline = PipelineDefinition(
            pipeline_id="fail-test",
            name="Failure Test",
            stages=[
                Stage("extract", "Extract", make_stage_func("data")),
                Stage("transform", "Transform", track_and_fail, dependencies=["extract"]),
                Stage("load", "Load", track_load, dependencies=["transform"]),
            ],
        )

        orchestrator.register_pipeline(pipeline)
        run = orchestrator.execute("fail-test")

        assert run.status == StageStatus.FAILED
        assert "load" not in executed, (
            "Load stage should NOT have executed because transform failed. "
            "Error propagation is broken."
        )
        assert run.stage_results["load"].status in (StageStatus.SKIPPED, StageStatus.FAILED)


class TestRetry:
    """Tests for retry logic — FAILING due to Bug #3."""

    def test_retry_resets_state(self, orchestrator: PipelineOrchestrator) -> None:
        """Retry should clear error state from previous attempt.
        FAILING: Bug #3 — error state persists across retries.
        """
        attempt = {"count": 0}

        def flaky_stage(ctx: dict) -> str:
            attempt["count"] += 1
            if attempt["count"] < 3:
                raise RuntimeError(f"Attempt {attempt['count']} failed")
            return "success"

        pipeline = PipelineDefinition(
            pipeline_id="retry-test",
            name="Retry Test",
            stages=[
                Stage("flaky", "Flaky Stage", flaky_stage, max_retries=3),
            ],
        )

        orchestrator.register_pipeline(pipeline)
        run = orchestrator.execute("retry-test")

        result = run.stage_results["flaky"]
        assert result.status == StageStatus.COMPLETED, (
            f"Stage should complete after retries, got {result.status}. "
            f"Error: {result.error}"
        )
        # After successful retry, error should be cleared
        assert result.error is None or result.status == StageStatus.COMPLETED


class TestScheduling:
    """Tests for pipeline scheduling — TODO: implement."""

    def test_schedule_pipeline(self, orchestrator: PipelineOrchestrator, simple_pipeline: PipelineDefinition) -> None:
        """TODO: Pipeline should be schedulable with cron expression."""
        orchestrator.register_pipeline(simple_pipeline)
        schedule = CronSchedule("every_hour")
        orchestrator.schedule_pipeline("simple", schedule)

        upcoming = orchestrator.get_next_scheduled_runs()
        assert len(upcoming) >= 1
        assert upcoming[0][0] == "simple"


class TestVersioning:
    """Tests for pipeline versioning — TODO: implement."""

    def test_register_versions(self, orchestrator: PipelineOrchestrator) -> None:
        """TODO: Registering updated pipeline should create new version."""
        v1 = PipelineDefinition(
            pipeline_id="versioned",
            name="Pipeline V1",
            stages=[Stage("s1", "Stage 1", make_stage_func("v1"))],
        )
        v2 = PipelineDefinition(
            pipeline_id="versioned",
            name="Pipeline V2",
            stages=[
                Stage("s1", "Stage 1", make_stage_func("v2")),
                Stage("s2", "Stage 2", make_stage_func("v2_s2"), dependencies=["s1"]),
            ],
        )

        ver1 = orchestrator.register_pipeline_version(v1)
        ver2 = orchestrator.register_pipeline_version(v2)
        assert ver1 == 1
        assert ver2 == 2

        p = orchestrator.get_pipeline_version("versioned", 1)
        assert p is not None
        assert len(p.stages) == 1


class TestExecutionHistory:
    """Tests for execution history — TODO: implement."""

    def test_history_recorded(self, orchestrator: PipelineOrchestrator, simple_pipeline: PipelineDefinition) -> None:
        """TODO: Execution runs should be recorded in history."""
        orchestrator.register_pipeline(simple_pipeline)
        orchestrator.execute("simple")
        orchestrator.execute("simple")

        history = orchestrator.get_execution_history("simple")
        assert len(history) == 2
        assert all("duration_ms" in h for h in history)

    def test_stage_metrics(self, orchestrator: PipelineOrchestrator, simple_pipeline: PipelineDefinition) -> None:
        """TODO: Should compute aggregate metrics per stage."""
        orchestrator.register_pipeline(simple_pipeline)
        orchestrator.execute("simple")

        metrics = orchestrator.get_stage_metrics("simple", "extract")
        assert "avg_duration_ms" in metrics
        assert "success_rate" in metrics
        assert metrics["total_runs"] == 1
