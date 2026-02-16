"""
Data Pipeline Orchestrator

Define and execute ETL pipelines with stage dependencies, error handling,
retry logic, and execution tracking.
"""

from __future__ import annotations

import time
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Stage:
    """A single stage in a pipeline."""
    stage_id: str
    name: str
    func: Callable[[dict[str, Any]], Any]
    dependencies: list[str] = field(default_factory=list)
    max_retries: int = 0
    timeout_seconds: Optional[float] = None


@dataclass
class StageResult:
    """Result of a single stage execution."""
    stage_id: str
    status: StageStatus
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    retry_count: int = 0


@dataclass
class PipelineDefinition:
    """Definition of a pipeline."""
    pipeline_id: str
    name: str
    stages: list[Stage] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PipelineRun:
    """A single execution run of a pipeline."""
    run_id: str
    pipeline_id: str
    stage_results: dict[str, StageResult] = field(default_factory=dict)
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CronSchedule:
    """Simple cron-like schedule representation."""

    def __init__(self, expression: str) -> None:
        """Parse a simplified cron expression.
        Supported: 'every_hour', 'every_minute', 'daily_at_HH:MM'
        """
        self.expression = expression

    def next_run(self, after: datetime) -> datetime:
        """Calculate the next run time after the given datetime."""
        raise NotImplementedError("Scheduling not implemented")


class PipelineOrchestrator:
    """Orchestrates ETL pipeline execution."""

    def __init__(self) -> None:
        self.pipelines: dict[str, PipelineDefinition] = {}
        self.runs: list[PipelineRun] = []
        self.schedules: dict[str, CronSchedule] = {}
        self._run_counter: int = 0
        # Track pipeline versions
        self.versions: dict[str, list[PipelineDefinition]] = defaultdict(list)

    def register_pipeline(self, pipeline: PipelineDefinition) -> None:
        """Register a pipeline definition."""
        self.pipelines[pipeline.pipeline_id] = pipeline

    def execute(self, pipeline_id: str) -> PipelineRun:
        """Execute a pipeline by running its stages in dependency order."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline '{pipeline_id}' not found")

        self._run_counter += 1
        run = PipelineRun(
            run_id=f"run-{self._run_counter}",
            pipeline_id=pipeline_id,
            started_at=datetime.now(timezone.utc),
        )
        run.status = StageStatus.RUNNING

        # Build execution order
        execution_order = self._resolve_order(pipeline)
        context: dict[str, Any] = {}

        # Track which stages have been executed
        executed: set[str] = set()

        for stage in execution_order:
            # BUG #1: Diamond dependency — a stage can appear multiple times
            # in execution_order because _resolve_order doesn't deduplicate.
            # If A -> B and A -> C, A appears once for B's deps and once for C's deps.
            result = self._execute_stage(stage, context, run)
            run.stage_results[stage.stage_id] = result

            if result.status == TaskStatus_COMPLETED:
                context[stage.stage_id] = result.output
                executed.add(stage.stage_id)

        run.completed_at = datetime.now(timezone.utc)
        run.status = (
            StageStatus.COMPLETED
            if all(r.status == StageStatus.COMPLETED for r in run.stage_results.values())
            else StageStatus.FAILED
        )
        self.runs.append(run)
        return run

    def _resolve_order(self, pipeline: PipelineDefinition) -> list[Stage]:
        """Resolve execution order using topological sort."""
        stage_map = {s.stage_id: s for s in pipeline.stages}
        order: list[Stage] = []
        # BUG #1: This recursive approach doesn't track visited nodes globally,
        # so shared dependencies are added multiple times.
        visited: set[str] = set()

        def visit(stage_id: str) -> None:
            # No check for 'stage_id in visited' before processing dependencies
            stage = stage_map[stage_id]
            for dep_id in stage.dependencies:
                if dep_id in stage_map:
                    visit(dep_id)
            order.append(stage)

        for stage in pipeline.stages:
            if stage.stage_id not in visited:
                visit(stage.stage_id)

        return order

    def _execute_stage(
        self,
        stage: Stage,
        context: dict[str, Any],
        run: PipelineRun,
    ) -> StageResult:
        """Execute a single stage."""
        result = StageResult(
            stage_id=stage.stage_id,
            status=StageStatus.RUNNING,
            start_time=datetime.now(timezone.utc),
        )

        # BUG #2: Doesn't check if dependencies have failed.
        # If a dependency failed, this stage should be skipped.
        # Currently it runs regardless of dependency status.

        retries = 0
        while retries <= stage.max_retries:
            try:
                output = stage.func(context)
                result.output = output
                result.status = StageStatus.COMPLETED
                break
            except Exception as e:
                # BUG #3: On retry, the error state from previous attempt persists.
                # result.status is still RUNNING but result.error has the old error.
                # Should reset result state before retry.
                result.error = str(e)
                retries += 1
                if retries > stage.max_retries:
                    result.status = StageStatus.FAILED

        result.end_time = datetime.now(timezone.utc)
        if result.start_time and result.end_time:
            result.duration_ms = (
                result.end_time - result.start_time
            ).total_seconds() * 1000
        result.retry_count = retries

        return result

    # -------------------------------------------------------------------------
    # TODO: Implement pipeline scheduling
    # -------------------------------------------------------------------------
    def schedule_pipeline(self, pipeline_id: str, schedule: CronSchedule) -> None:
        """Schedule a pipeline for recurring execution."""
        raise NotImplementedError("Scheduling not implemented")

    def get_next_scheduled_runs(self) -> list[tuple[str, datetime]]:
        """Get upcoming scheduled pipeline runs."""
        raise NotImplementedError("Scheduling not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement pipeline versioning
    # -------------------------------------------------------------------------
    def register_pipeline_version(self, pipeline: PipelineDefinition) -> int:
        """Register a new version of a pipeline. Returns the version number."""
        raise NotImplementedError("Versioning not implemented")

    def get_pipeline_version(self, pipeline_id: str, version: int) -> Optional[PipelineDefinition]:
        """Get a specific version of a pipeline."""
        raise NotImplementedError("Versioning not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement execution history and metrics
    # -------------------------------------------------------------------------
    def get_execution_history(
        self, pipeline_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get execution history for a pipeline.
        Returns list of {"run_id": str, "status": str, "started_at": str,
        "duration_ms": float, "stages": dict}.
        """
        raise NotImplementedError("Execution history not implemented")

    def get_stage_metrics(
        self, pipeline_id: str, stage_id: str
    ) -> dict[str, Any]:
        """Get aggregated metrics for a stage across runs.
        Returns {"avg_duration_ms": float, "success_rate": float,
        "total_runs": int, "last_run": str}.
        """
        raise NotImplementedError("Stage metrics not implemented")


# Alias for convenience in execute method (avoids import-like reference)
TaskStatus_COMPLETED = StageStatus.COMPLETED
