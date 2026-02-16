# Task 02: Consistent Hashing Ring

**Time Limit: 60 minutes**

## Overview

You are given an implementation of a consistent hashing ring used to distribute
keys across a set of nodes with virtual nodes. This is a core building block for
distributed systems like Dynamo, Cassandra, and memcached.

## Current State

The code supports adding/removing nodes, looking up which node owns a given key,
and using virtual nodes for better distribution. However, there are several bugs
that break correctness.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Node removal doesn't rehash affected keys** — When a node is removed, keys
   that were assigned to it should be reassigned to the next node on the ring,
   but the current implementation leaves orphaned entries.

2. **Virtual nodes cluster together** — The hash function for virtual nodes produces
   clustered positions on the ring instead of evenly distributed ones.

3. **Lookup doesn't handle empty ring** — Looking up a key on an empty ring causes
   an unhandled error instead of returning None.

## Features to Implement

1. **Replication Factor** — Support storing each key on N consecutive nodes on the
   ring (replication_factor parameter).

2. **Weighted Nodes** — Allow nodes to have different weights that control how many
   virtual nodes they get (more weight = more virtual nodes = more keys).

3. **Ring Statistics** — Compute a balance score showing how evenly keys are
   distributed (0.0 = perfectly balanced, 1.0 = completely unbalanced).

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
