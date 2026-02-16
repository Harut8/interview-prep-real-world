"""Tests for the MapReduce Framework."""

import pytest
from app import (
    MapReduceEngine,
    MapReduceJob,
    JobStatus,
    word_count_mapper,
    word_count_reducer,
    word_count_combiner,
)


@pytest.fixture
def engine() -> MapReduceEngine:
    return MapReduceEngine()


@pytest.fixture
def sample_docs() -> dict[str, str]:
    return {
        "doc1": "the quick brown fox jumps over the lazy dog",
        "doc2": "the fox is quick and the dog is lazy",
        "doc3": "brown fox brown dog brown cat",
    }


class TestWordCount:
    """Basic word count tests — some fail due to bugs."""

    def test_basic_word_count(self, engine: MapReduceEngine, sample_docs: dict) -> None:
        """Basic word count without combiner should work."""
        job = MapReduceJob(
            name="word-count",
            mapper=word_count_mapper,
            reducer=word_count_reducer,
            num_reducers=2,
        )
        result = engine.run(job, sample_docs)
        assert result.status == JobStatus.COMPLETED
        assert result.output["the"] == 4  # "the" appears 4 times total
        assert result.output["fox"] == 3
        assert result.output["brown"] == 4

    def test_word_count_with_combiner(self, engine: MapReduceEngine, sample_docs: dict) -> None:
        """Word count WITH combiner should produce the same results as without.
        FAILING: Bug #1 — combiner loses values due to overwrite instead of append.
        """
        job = MapReduceJob(
            name="word-count-combined",
            mapper=word_count_mapper,
            reducer=word_count_reducer,
            combiner=word_count_combiner,
            num_reducers=2,
        )
        result = engine.run(job, sample_docs)
        assert result.status == JobStatus.COMPLETED
        # With combiner, results should be identical to without
        assert result.output["the"] == 4, (
            f"Expected 'the' count=4, got {result.output.get('the')}. "
            f"Combiner may be losing values."
        )
        assert result.output["brown"] == 4

    def test_partition_distributes_evenly(self, engine: MapReduceEngine) -> None:
        """Keys should be distributed across reducers, not all in one.
        FAILING: Bug #2 — partition function uses len(key), so same-length keys
        go to the same reducer.
        """
        job = MapReduceJob(
            name="partition-test",
            mapper=word_count_mapper,
            reducer=word_count_reducer,
            num_reducers=3,
        )
        docs = {
            "d1": "cat dog fox bat rat ant bee cow hen owl pig yak",
        }
        result = engine.run(job, docs)
        assert result.status == JobStatus.COMPLETED

        # Check that the partition function actually distributes different 3-letter words
        # to different reducers
        partitions_used = set()
        for word in ["cat", "dog", "fox", "bat", "rat", "ant", "bee", "cow", "hen"]:
            partitions_used.add(engine._default_partition(word, 3))

        assert len(partitions_used) > 1, (
            f"All 3-letter words mapped to same partition(s): {partitions_used}. "
            f"Partition function should use hash(key), not len(key)."
        )

    def test_output_sorted_by_key(self, engine: MapReduceEngine, sample_docs: dict) -> None:
        """Reduce output should process keys in sorted order.
        FAILING: Bug #3 — intermediate results are not sorted before reduce.
        """
        processed_keys: list[str] = []
        original_reducer = word_count_reducer

        def tracking_reducer(key: str, values: list[int]) -> int:
            processed_keys.append(key)
            return original_reducer(key, values)

        job = MapReduceJob(
            name="sorted-test",
            mapper=word_count_mapper,
            reducer=tracking_reducer,
            num_reducers=1,  # Single reducer to check global sort
        )
        result = engine.run(job, sample_docs)
        assert result.status == JobStatus.COMPLETED
        assert processed_keys == sorted(processed_keys), (
            f"Keys were not processed in sorted order. Got: {processed_keys[:10]}..."
        )


class TestFaultTolerance:
    """Tests for fault tolerance — TODO: implement."""

    def test_retry_on_mapper_failure(self, engine: MapReduceEngine) -> None:
        """TODO: Mapper that fails once then succeeds should complete with retries."""
        call_count = {"value": 0}

        def flaky_mapper(key: str, value: str) -> list[tuple[str, int]]:
            call_count["value"] += 1
            if call_count["value"] == 1:
                raise RuntimeError("Transient failure")
            return [(w, 1) for w in value.split()]

        job = MapReduceJob(
            name="flaky-job",
            mapper=flaky_mapper,
            reducer=word_count_reducer,
            max_retries=3,
        )
        result = engine.run(job, {"doc1": "hello world"})
        assert result.status == JobStatus.COMPLETED

    def test_fail_after_max_retries(self, engine: MapReduceEngine) -> None:
        """TODO: Job should fail if mapper exceeds max retries."""
        def always_fail_mapper(key: str, value: str) -> list[tuple[str, int]]:
            raise RuntimeError("Permanent failure")

        job = MapReduceJob(
            name="fail-job",
            mapper=always_fail_mapper,
            reducer=word_count_reducer,
            max_retries=2,
        )
        result = engine.run(job, {"doc1": "hello"})
        assert result.status == JobStatus.FAILED


class TestCustomPartitioner:
    """Tests for custom partitioner — TODO: implement."""

    def test_custom_partitioner_used(self, engine: MapReduceEngine) -> None:
        """TODO: When a custom partitioner is provided, it should be used."""
        def first_letter_partitioner(key: str, num_reducers: int) -> int:
            return ord(key[0]) % num_reducers

        job = MapReduceJob(
            name="custom-partition",
            mapper=word_count_mapper,
            reducer=word_count_reducer,
            partitioner=first_letter_partitioner,
            num_reducers=3,
        )
        result = engine.run(job, {"d1": "apple banana cherry"})
        assert result.status == JobStatus.COMPLETED
        assert "apple" in result.output
