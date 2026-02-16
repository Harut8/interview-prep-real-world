"""
Distributed Counter Service

Eventually-consistent counter using CRDT (PN-Counter) semantics.
Each node tracks its own increments and decrements, and nodes merge
state by taking the maximum per-node count.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CounterState:
    """State of a PN-Counter CRDT.
    p_counter: per-node positive counts (increments)
    n_counter: per-node negative counts (decrements)
    Value = sum(p_counter.values()) - sum(n_counter.values())
    """
    p_counter: dict[str, int] = field(default_factory=dict)
    n_counter: dict[str, int] = field(default_factory=dict)


class DistributedCounter:
    """A PN-Counter CRDT for distributed counting."""

    def __init__(self, node_id: Optional[str] = None) -> None:
        # BUG #3: If node_id is None, generates a random one, which is fine.
        # But there's no validation to prevent two counters from being created
        # with the same node_id. When they merge, the second node's state
        # overwrites the first's instead of being additive.
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.state = CounterState()

    def increment(self, amount: int = 1) -> None:
        """Increment the counter by amount on this node."""
        if amount < 0:
            raise ValueError("Increment amount must be non-negative")
        current = self.state.p_counter.get(self.node_id, 0)
        self.state.p_counter[self.node_id] = current + amount

    def decrement(self, amount: int = 1) -> None:
        """Decrement the counter by amount on this node."""
        if amount < 0:
            raise ValueError("Decrement amount must be non-negative")
        # BUG #2: Subtracts from p_counter instead of adding to n_counter.
        # In a PN-Counter, decrements should be tracked in n_counter.
        # Subtracting from p_counter corrupts the state because merges
        # take max(p_counter) — the decrement would be lost after merge.
        current = self.state.p_counter.get(self.node_id, 0)
        self.state.p_counter[self.node_id] = current - amount

    def value(self) -> int:
        """Get the current counter value."""
        p_total = sum(self.state.p_counter.values())
        n_total = sum(self.state.n_counter.values())
        return p_total - n_total

    def merge(self, other: "DistributedCounter") -> None:
        """Merge state from another counter (CRDT merge)."""
        # BUG #1: Adds values instead of taking max.
        # CRDT G-Counter merge requires taking max(local, remote) per node.
        # Adding causes double-counting when the same increments are merged
        # from multiple paths.

        # Merge p_counters
        for node_id, count in other.state.p_counter.items():
            current = self.state.p_counter.get(node_id, 0)
            self.state.p_counter[node_id] = current + count  # BUG: should be max(current, count)

        # Merge n_counters
        for node_id, count in other.state.n_counter.items():
            current = self.state.n_counter.get(node_id, 0)
            self.state.n_counter[node_id] = current + count  # BUG: should be max(current, count)

    # -------------------------------------------------------------------------
    # TODO: Implement counter snapshots
    # -------------------------------------------------------------------------
    def snapshot(self) -> str:
        """Serialize the counter state to a JSON string."""
        raise NotImplementedError("Snapshots not implemented")

    @classmethod
    def from_snapshot(cls, data: str) -> "DistributedCounter":
        """Restore a counter from a serialized snapshot."""
        raise NotImplementedError("Snapshot restoration not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement garbage collection
    # -------------------------------------------------------------------------
    def garbage_collect(self, known_nodes: set[str]) -> None:
        """Compact p and n counters when all nodes have seen the decrements.
        If all nodes in known_nodes have entries in both p and n counters,
        we can subtract the min(n_counter) from both sides to save space.
        """
        raise NotImplementedError("Garbage collection not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement bounded counter
    # -------------------------------------------------------------------------


class BoundedCounter:
    """A counter with min and max bounds that cannot be exceeded.
    Uses a PN-Counter internally but enforces bounds on increment/decrement.
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        min_value: int = 0,
        max_value: int = 100,
    ) -> None:
        self.counter = DistributedCounter(node_id=node_id)
        self.min_value = min_value
        self.max_value = max_value

    def increment(self, amount: int = 1) -> bool:
        """Increment if it wouldn't exceed max_value. Returns True if successful."""
        raise NotImplementedError("Bounded increment not implemented")

    def decrement(self, amount: int = 1) -> bool:
        """Decrement if it wouldn't go below min_value. Returns True if successful."""
        raise NotImplementedError("Bounded decrement not implemented")

    def value(self) -> int:
        return self.counter.value()
