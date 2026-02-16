"""Tests for the Distributed Counter Service."""

import pytest
from app import DistributedCounter, BoundedCounter


class TestBasicOperations:
    """Tests for basic counter operations."""

    def test_increment(self) -> None:
        """Simple increment should work."""
        c = DistributedCounter(node_id="node1")
        c.increment(5)
        assert c.value() == 5

    def test_multiple_increments(self) -> None:
        """Multiple increments should accumulate."""
        c = DistributedCounter(node_id="node1")
        c.increment(3)
        c.increment(7)
        assert c.value() == 10

    def test_initial_value_zero(self) -> None:
        """New counter should have value 0."""
        c = DistributedCounter(node_id="node1")
        assert c.value() == 0


class TestDecrement:
    """Tests for decrement — FAILING due to Bug #2."""

    def test_decrement_tracked_separately(self) -> None:
        """Decrements should be tracked in n_counter, not subtracted from p_counter.
        FAILING: Bug #2 — subtracts from p_counter instead.
        """
        c = DistributedCounter(node_id="node1")
        c.increment(10)
        c.decrement(3)

        assert c.value() == 7
        # The key check: p_counter should still be 10, n_counter should be 3
        assert c.state.p_counter.get("node1") == 10, (
            f"p_counter should be 10 (increments only), "
            f"got {c.state.p_counter.get('node1')}. "
            f"Decrements should go to n_counter."
        )
        assert c.state.n_counter.get("node1") == 3, (
            f"n_counter should be 3, got {c.state.n_counter.get('node1')}. "
            f"Decrements should be tracked in n_counter."
        )

    def test_decrement_survives_merge(self) -> None:
        """Decrement should not be lost after merging.
        FAILING: Bug #2 — since decrement modifies p_counter, the merge (which
        takes max) will restore the higher p_counter value from the remote,
        effectively undoing the decrement.
        """
        c1 = DistributedCounter(node_id="node1")
        c2 = DistributedCounter(node_id="node2")

        c1.increment(10)
        c2.merge(c1)  # c2 now knows c1 has p=10

        c1.decrement(3)  # c1 should be value=7
        c2.merge(c1)  # After merge, c2 should also show value=7

        assert c2.value() == 7, (
            f"After merge, value should be 7, got {c2.value()}. "
            f"Decrement was lost during merge because it was subtracted from p_counter."
        )


class TestMerge:
    """Tests for CRDT merge — FAILING due to Bug #1."""

    def test_merge_concurrent_increments(self) -> None:
        """Merge of independent counters should sum their values."""
        c1 = DistributedCounter(node_id="node1")
        c2 = DistributedCounter(node_id="node2")

        c1.increment(5)
        c2.increment(3)

        c1.merge(c2)
        assert c1.value() == 8  # 5 + 3

    def test_merge_idempotent(self) -> None:
        """Merging the same state twice should not change the value.
        FAILING: Bug #1 — merge adds instead of taking max, so double merge doubles.
        """
        c1 = DistributedCounter(node_id="node1")
        c2 = DistributedCounter(node_id="node2")

        c1.increment(5)
        c2.increment(3)

        c1.merge(c2)
        first_value = c1.value()

        c1.merge(c2)  # Merge again — should be idempotent
        assert c1.value() == first_value, (
            f"Merging same state twice changed value from {first_value} to {c1.value()}. "
            f"CRDT merge must be idempotent (use max, not addition)."
        )

    def test_merge_three_nodes_convergence(self) -> None:
        """Three nodes merging pairwise should all converge to same value.
        FAILING: Bug #1 — addition-based merge causes different values depending
        on merge order.
        """
        c1 = DistributedCounter(node_id="node1")
        c2 = DistributedCounter(node_id="node2")
        c3 = DistributedCounter(node_id="node3")

        c1.increment(10)
        c2.increment(20)
        c3.increment(30)

        # Merge in different orders
        c1.merge(c2)
        c1.merge(c3)

        c2.merge(c1)
        c3.merge(c1)

        assert c1.value() == c2.value() == c3.value() == 60, (
            f"All nodes should converge to 60. Got c1={c1.value()}, "
            f"c2={c2.value()}, c3={c3.value()}"
        )


class TestNodeIdCollision:
    """Tests for node ID collision — related to Bug #3."""

    def test_unique_node_ids(self) -> None:
        """Two counters with the same node ID should be detected or handled.
        FAILING: Bug #3 — no validation, data is silently corrupted.
        """
        c1 = DistributedCounter(node_id="same-id")
        c2 = DistributedCounter(node_id="same-id")

        c1.increment(5)
        c2.increment(10)

        # After merge, the value should be 15 (both nodes contributed)
        # But with same node_id, one overwrites the other
        c1.merge(c2)
        # With the add-bug, this becomes 15 by accident, but with max it becomes 10
        # The real fix: prevent or detect same-node-id scenario
        # For this test: at minimum, document the expected behavior


class TestSnapshots:
    """Tests for counter snapshots — TODO: implement."""

    def test_snapshot_roundtrip(self) -> None:
        """TODO: Counter state should survive serialization roundtrip."""
        c = DistributedCounter(node_id="node1")
        c.increment(42)

        snapshot = c.snapshot()
        restored = DistributedCounter.from_snapshot(snapshot)
        assert restored.value() == 42
        assert restored.node_id == "node1"

    def test_snapshot_format_is_json(self) -> None:
        """TODO: Snapshot should be valid JSON."""
        import json
        c = DistributedCounter(node_id="node1")
        c.increment(10)
        snapshot = c.snapshot()
        parsed = json.loads(snapshot)
        assert "p_counter" in parsed


class TestBoundedCounter:
    """Tests for bounded counter — TODO: implement."""

    def test_bounded_max(self) -> None:
        """TODO: Counter should not exceed max_value."""
        bc = BoundedCounter(node_id="node1", min_value=0, max_value=10)
        assert bc.increment(8) is True
        assert bc.increment(5) is False  # Would exceed 10
        assert bc.value() == 8

    def test_bounded_min(self) -> None:
        """TODO: Counter should not go below min_value."""
        bc = BoundedCounter(node_id="node1", min_value=0, max_value=10)
        bc.increment(5)
        assert bc.decrement(3) is True
        assert bc.decrement(5) is False  # Would go below 0
        assert bc.value() == 2


class TestGarbageCollection:
    """Tests for garbage collection — TODO: implement."""

    def test_gc_compacts_counters(self) -> None:
        """TODO: GC should compact counters when safe to do so."""
        c = DistributedCounter(node_id="node1")
        c.increment(100)
        c.state.n_counter["node1"] = 30  # Manually set for test

        c.garbage_collect(known_nodes={"node1"})

        # After GC, values should be reduced but net value preserved
        assert c.value() == 70
