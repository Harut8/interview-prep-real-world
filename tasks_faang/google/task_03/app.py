"""
MapReduce Framework

A simple single-machine MapReduce implementation supporting user-defined map/reduce
functions, combiners, and partitioning.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Type aliases
MapFunc = Callable[[str, Any], list[tuple[str, Any]]]
ReduceFunc = Callable[[str, list[Any]], Any]
CombineFunc = Callable[[str, list[Any]], Any]
PartitionFunc = Callable[[str, int], int]


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MapReduceJob:
    """Configuration for a MapReduce job."""
    name: str
    mapper: MapFunc
    reducer: ReduceFunc
    combiner: Optional[CombineFunc] = None
    partitioner: Optional[PartitionFunc] = None
    num_reducers: int = 3
    max_retries: int = 0  # For fault tolerance feature


@dataclass
class JobResult:
    """Result of a MapReduce job execution."""
    status: JobStatus
    output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    progress: float = 0.0  # 0.0 to 1.0


class MapReduceEngine:
    """Single-machine MapReduce execution engine."""

    def __init__(self) -> None:
        self.progress_callback: Optional[Callable[[float, str], None]] = None

    def run(self, job: MapReduceJob, input_data: dict[str, Any]) -> JobResult:
        """Execute a MapReduce job on the given input data."""
        result = JobResult(status=JobStatus.RUNNING)

        try:
            # Phase 1: Map
            intermediate = self._map_phase(job, input_data, result)
            if result.status == JobStatus.FAILED:
                return result

            # Phase 2: Combine (optional)
            if job.combiner:
                intermediate = self._combine_phase(job, intermediate)

            # Phase 3: Shuffle & Sort
            partitioned = self._shuffle_phase(job, intermediate)

            # Phase 4: Reduce
            output = self._reduce_phase(job, partitioned, result)

            result.output = output
            result.status = JobStatus.COMPLETED
            result.progress = 1.0

        except Exception as e:
            result.status = JobStatus.FAILED
            result.errors.append(str(e))

        return result

    def _map_phase(
        self,
        job: MapReduceJob,
        input_data: dict[str, Any],
        result: JobResult,
    ) -> list[tuple[str, Any]]:
        """Run the map function on each input record."""
        intermediate: list[tuple[str, Any]] = []
        total = len(input_data)

        for i, (key, value) in enumerate(input_data.items()):
            try:
                mapped = job.mapper(key, value)
                intermediate.extend(mapped)
            except Exception as e:
                # No retry logic — just fails immediately
                result.status = JobStatus.FAILED
                result.errors.append(f"Mapper failed on key '{key}': {e}")
                return intermediate

            if self.progress_callback:
                self.progress_callback((i + 1) / total * 0.5, "map")

        return intermediate

    def _combine_phase(
        self, job: MapReduceJob, intermediate: list[tuple[str, Any]]
    ) -> list[tuple[str, Any]]:
        """Apply combiner to locally aggregate intermediate values."""
        if not job.combiner:
            return intermediate

        grouped: dict[str, Any] = {}
        for key, value in intermediate:
            # BUG #1: Overwrites instead of appending. Each key should collect
            # all its values into a list, then the combiner processes the list.
            # Instead, this only keeps the last value seen for each key.
            grouped[key] = value

        combined: list[tuple[str, Any]] = []
        for key, value in grouped.items():
            # Because of the bug above, `value` is a single item, not a list
            combined_value = job.combiner(key, [value])
            combined.append((key, combined_value))

        return combined

    def _shuffle_phase(
        self,
        job: MapReduceJob,
        intermediate: list[tuple[str, Any]],
    ) -> dict[int, dict[str, list[Any]]]:
        """Partition and sort intermediate key-value pairs for reducers."""
        partitioned: dict[int, dict[str, list[Any]]] = {
            i: defaultdict(list) for i in range(job.num_reducers)
        }

        for key, value in intermediate:
            partition = self._default_partition(key, job.num_reducers)
            partitioned[partition][key].append(value)

        # BUG #3: Missing sort step. The reduce phase expects keys to be in
        # sorted order within each partition, but we never sort them.
        # The dict iteration order is insertion order, not sorted order.
        return partitioned

    def _reduce_phase(
        self,
        job: MapReduceJob,
        partitioned: dict[int, dict[str, list[Any]]],
        result: JobResult,
    ) -> dict[str, Any]:
        """Run the reduce function on each group of values."""
        output: dict[str, Any] = {}
        total_partitions = len(partitioned)

        for i, (partition_id, groups) in enumerate(partitioned.items()):
            for key, values in groups.items():
                output[key] = job.reducer(key, values)

            if self.progress_callback:
                self.progress_callback(0.5 + (i + 1) / total_partitions * 0.5, "reduce")

        return output

    def _default_partition(self, key: str, num_reducers: int) -> int:
        """Hash-based partitioning of keys to reducers."""
        # BUG #2: Using len(key) as the hash is terrible — all keys of the same
        # length go to the same reducer. Should use hash(key) or similar.
        return len(key) % num_reducers

    # -------------------------------------------------------------------------
    # TODO: Implement fault tolerance (retry failed mappers)
    # -------------------------------------------------------------------------
    def _map_with_retry(
        self,
        job: MapReduceJob,
        key: str,
        value: Any,
        max_retries: int,
    ) -> list[tuple[str, Any]]:
        """Run mapper with retry logic. Retry up to max_retries times on failure."""
        raise NotImplementedError("Fault tolerance not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement progress tracking
    # -------------------------------------------------------------------------
    def get_progress(self) -> dict[str, Any]:
        """Return current progress of the running job.
        Should include: phase (map/reduce), percentage, tasks completed/total.
        """
        raise NotImplementedError("Progress tracking not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement custom partitioner support
    # -------------------------------------------------------------------------
    def _partition_with_custom(
        self,
        job: MapReduceJob,
        key: str,
        num_reducers: int,
    ) -> int:
        """Use custom partitioner if provided, otherwise use default."""
        raise NotImplementedError("Custom partitioner support not implemented")


# --- Example map/reduce functions for testing ---

def word_count_mapper(doc_id: str, text: str) -> list[tuple[str, int]]:
    """Map function for word count."""
    words = text.lower().split()
    return [(word, 1) for word in words]


def word_count_reducer(word: str, counts: list[int]) -> int:
    """Reduce function for word count."""
    return sum(counts)


def word_count_combiner(word: str, counts: list[int]) -> int:
    """Combiner for word count — same as reducer."""
    return sum(counts)
