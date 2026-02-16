# Task 09: Distributed Counter Service

**Time Limit: 60 minutes**

## Overview

You are given an eventually-consistent distributed counter using CRDT (Conflict-free
Replicated Data Type) semantics. Each node can independently increment/decrement
its counter, and nodes can merge their state to converge to the correct value.

This uses a PN-Counter (Positive-Negative Counter) CRDT, where increments and
decrements are tracked separately per node.

## Current State

The counter supports increment, decrement, get value, and merge operations.
However, there are bugs in the merge function, decrement handling, and node ID
management.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Merge doesn't handle concurrent increments correctly** — When merging state
   from another node, the merge function adds values instead of taking the max
   per node (which is the correct CRDT merge for G-Counters).

2. **Decrement can cause counter to go negative** — The PN-Counter should track
   negative counts separately, but the current implementation subtracts directly
   from the positive counter, which can cause incorrect state after merges.

3. **Node ID collision causes data loss** — When two nodes have the same ID, their
   state overwrites each other during merge instead of being properly isolated.

## Features to Implement

1. **Counter Snapshots** — Save and restore counter state to/from a serializable
   format.

2. **Garbage Collection of Tombstones** — When all nodes have seen a decrement,
   compact the P and N counters to save memory.

3. **Bounded Counter** — Support counters with minimum and maximum bounds that
   cannot be exceeded.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
