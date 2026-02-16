"""Tests for the Consistent Hashing Ring."""

import pytest
from app import ConsistentHashRing, Node


@pytest.fixture
def ring() -> ConsistentHashRing:
    """Create a ring with 3 nodes."""
    r = ConsistentHashRing(num_virtual_nodes=100)
    r.add_node(Node("node-a", "10.0.0.1", 8080))
    r.add_node(Node("node-b", "10.0.0.2", 8080))
    r.add_node(Node("node-c", "10.0.0.3", 8080))
    return r


class TestBasicOperations:
    """Tests for basic ring operations — some pass, some fail due to bugs."""

    def test_add_node(self, ring: ConsistentHashRing) -> None:
        """Adding a node should register it in the ring."""
        assert "node-a" in ring.nodes
        assert "node-b" in ring.nodes
        assert len(ring.sorted_keys) == 300  # 3 nodes * 100 virtual nodes

    def test_get_node_deterministic(self, ring: ConsistentHashRing) -> None:
        """Same key should always map to the same node."""
        node1 = ring.get_node("user:12345")
        node2 = ring.get_node("user:12345")
        assert node1 == node2

    def test_get_node_empty_ring(self) -> None:
        """Looking up a key on an empty ring should return None, not crash.
        FAILING: Bug #3 — crashes with IndexError on empty ring.
        """
        empty_ring = ConsistentHashRing()
        result = empty_ring.get_node("some-key")
        assert result is None

    def test_remove_node_cleanup(self, ring: ConsistentHashRing) -> None:
        """After removing a node, its keys should be reassigned.
        FAILING: Bug #1 — node removal doesn't clean up ring entries.
        """
        key = "test-key-42"
        original_node = ring.get_node(key)

        # Remove the node that owns this key
        ring.remove_node(original_node)

        # The key should now map to a different, existing node
        new_node = ring.get_node(key)
        assert new_node is not None
        assert new_node != original_node
        assert new_node in ring.nodes

    def test_remove_reduces_ring_size(self, ring: ConsistentHashRing) -> None:
        """Removing a node should reduce the number of entries in sorted_keys.
        FAILING: Bug #1 — sorted_keys not cleaned up.
        """
        initial_size = len(ring.sorted_keys)
        ring.remove_node("node-b")
        assert len(ring.sorted_keys) == initial_size - 100


class TestDistribution:
    """Tests for key distribution quality — FAILING due to clustering bug."""

    def test_virtual_nodes_spread(self, ring: ConsistentHashRing) -> None:
        """Virtual node positions should be well-distributed across the ring.
        FAILING: Bug #2 — hash function limits ring to 2^16 positions, causing clustering.
        """
        # Check that positions span a wide range
        min_pos = min(ring.sorted_keys)
        max_pos = max(ring.sorted_keys)
        ring_range = max_pos - min_pos

        # With a good hash function, the range should be very large (close to 2^128 for MD5)
        # With the bug, it's capped at 2^16 = 65536
        assert ring_range > 2**32, (
            f"Ring range is only {ring_range}. Virtual node positions are clustered. "
            f"Check the hash function — positions should span a much larger range."
        )

    def test_even_distribution(self, ring: ConsistentHashRing) -> None:
        """Keys should be roughly evenly distributed across nodes."""
        counts: dict[str, int] = {"node-a": 0, "node-b": 0, "node-c": 0}
        for i in range(3000):
            node = ring.get_node(f"key-{i}")
            if node in counts:
                counts[node] += 1

        # Each node should get roughly 1000 keys (1/3 of 3000)
        for node_id, count in counts.items():
            assert 500 < count < 1500, (
                f"{node_id} got {count} keys, expected ~1000. Distribution is uneven."
            )


class TestReplication:
    """Tests for replication feature — TODO: implement."""

    def test_get_nodes_for_replication(self, ring: ConsistentHashRing) -> None:
        """TODO: get_nodes_for_key should return N distinct nodes for replication."""
        nodes = ring.get_nodes_for_key("user:999", count=2)
        assert len(nodes) == 2
        assert nodes[0] != nodes[1]  # Must be distinct nodes

    def test_replication_wraps_around_ring(self, ring: ConsistentHashRing) -> None:
        """TODO: Replication should wrap around the ring if needed."""
        nodes = ring.get_nodes_for_key("user:999", count=3)
        assert len(nodes) == 3
        assert len(set(nodes)) == 3  # All distinct


class TestWeightedNodes:
    """Tests for weighted node support — TODO: implement."""

    def test_weighted_node_gets_more_keys(self) -> None:
        """TODO: A node with weight=3 should get ~3x the keys of weight=1."""
        r = ConsistentHashRing(num_virtual_nodes=100)
        r.add_weighted_node(Node("light", "10.0.0.1", 8080, weight=1))
        r.add_weighted_node(Node("heavy", "10.0.0.2", 8080, weight=3))

        counts = {"light": 0, "heavy": 0}
        for i in range(4000):
            node = r.get_node(f"key-{i}")
            if node in counts:
                counts[node] += 1

        ratio = counts["heavy"] / max(counts["light"], 1)
        assert 2.0 < ratio < 4.0, f"Heavy/light ratio should be ~3, got {ratio:.1f}"


class TestBalanceScore:
    """Tests for balance score — TODO: implement."""

    def test_balance_score_range(self, ring: ConsistentHashRing) -> None:
        """TODO: Balance score should be between 0 and 1."""
        score = ring.get_balance_score()
        assert 0.0 <= score <= 1.0

    def test_single_node_perfect_balance(self) -> None:
        """TODO: A ring with one node should be perfectly balanced (score ~0)."""
        r = ConsistentHashRing(num_virtual_nodes=100)
        r.add_node(Node("only-node", "10.0.0.1", 8080))
        score = r.get_balance_score()
        assert score < 0.01
