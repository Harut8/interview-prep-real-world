"""
Consistent Hashing Ring

Distributes keys across a set of nodes using consistent hashing with virtual nodes.
Used as a building block for distributed storage systems.
"""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    """Represents a server/node in the ring."""
    node_id: str
    host: str
    port: int
    weight: int = 1  # Used for weighted node support


class ConsistentHashRing:
    """Consistent hashing ring with virtual nodes."""

    def __init__(self, num_virtual_nodes: int = 150, replication_factor: int = 1) -> None:
        self.num_virtual_nodes = num_virtual_nodes
        self.replication_factor = replication_factor
        self.ring: dict[int, str] = {}  # hash position -> node_id
        self.sorted_keys: list[int] = []
        self.nodes: dict[str, Node] = {}

    def _hash(self, key: str) -> int:
        """Hash a key to a position on the ring."""
        digest = hashlib.md5(key.encode()).hexdigest()
        return int(digest, 16)

    def _virtual_node_hash(self, node_id: str, replica_index: int) -> int:
        """Hash a virtual node to a position on the ring."""
        # BUG #2: Using a bad hash strategy that causes clustering.
        # Simply appending the index number means "node1-1", "node1-2", etc.
        # produce similar hashes because MD5 of similar strings are NOT guaranteed
        # to be far apart, BUT the real issue is we're using str(replica_index)
        # which for large numbers still works with MD5. The actual bug is using
        # a simple concatenation that doesn't mix well:
        key = f"{node_id}{replica_index}"  # Should be f"{node_id}-{replica_index}" with a separator
        # Actually, the real clustering bug: we're using the raw integer index
        # but hashing only the last few chars effectively:
        return self._hash(key) % (2**16)  # BUG: Modulo 2^16 severely limits ring space
        # Should be: return self._hash(f"{node_id}-{replica_index}")

    def add_node(self, node: Node) -> None:
        """Add a node to the ring with its virtual nodes."""
        if node.node_id in self.nodes:
            return
        self.nodes[node.node_id] = node
        for i in range(self.num_virtual_nodes):
            hash_val = self._virtual_node_hash(node.node_id, i)
            self.ring[hash_val] = node.node_id
            bisect.insort(self.sorted_keys, hash_val)

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its virtual nodes from the ring."""
        if node_id not in self.nodes:
            return
        # BUG #1: Only removes from self.nodes but doesn't clean up the ring
        # and sorted_keys. Keys assigned to this node become orphaned.
        del self.nodes[node_id]
        # Missing: removal of virtual node entries from self.ring and self.sorted_keys
        # The entries in self.ring still point to the deleted node_id.

    def get_node(self, key: str) -> Optional[str]:
        """Find which node a key belongs to."""
        # BUG #3: Doesn't handle empty ring — will crash on empty sorted_keys
        hash_val = self._hash(key)
        idx = bisect.bisect_right(self.sorted_keys, hash_val)
        if idx == len(self.sorted_keys):
            idx = 0
        return self.ring[self.sorted_keys[idx]]

    def get_nodes_for_key(self, key: str, count: Optional[int] = None) -> list[str]:
        """Get multiple nodes for a key (for replication).
        Returns `count` distinct nodes starting from the key's position on the ring.
        """
        # TODO: Implement replication support — return `count` unique consecutive nodes
        raise NotImplementedError("Replication support not implemented")

    def get_balance_score(self) -> float:
        """Compute how evenly keys would be distributed across nodes.
        Returns a score from 0.0 (perfectly balanced) to 1.0 (completely unbalanced).
        Uses the coefficient of variation of the arc lengths assigned to each node.
        """
        # TODO: Implement balance score
        raise NotImplementedError("Balance score not implemented")

    def add_weighted_node(self, node: Node) -> None:
        """Add a node with weight — more weight means more virtual nodes."""
        # TODO: Implement weighted node support
        # A node with weight=2 should get 2x the virtual nodes compared to weight=1
        raise NotImplementedError("Weighted node support not implemented")
