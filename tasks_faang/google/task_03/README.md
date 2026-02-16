# Task 03: MapReduce Framework

**Time Limit: 60 minutes**

## Overview

You are given a simple single-machine MapReduce implementation. It supports
user-defined map and reduce functions, combiners for local aggregation,
and partitioning of intermediate keys across reducers.

## Current State

The framework can run basic MapReduce jobs (word count, etc.) but has bugs in
the combiner, partitioner, and intermediate sorting that cause incorrect results.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Combiner doesn't handle multi-value keys** — The combiner is supposed to
   locally aggregate values for the same key before sending to reducers, but it
   only keeps the last value instead of aggregating all values.

2. **Partition function distributes keys unevenly** — The hash-based partitioner
   uses a flawed modulo that causes most keys to go to the same reducer.

3. **Intermediate results not sorted before reduce** — The reduce phase expects
   values grouped by key in sorted order, but the shuffle step doesn't sort.

## Features to Implement

1. **Fault Tolerance** — If a mapper raises an exception, retry it up to N times
   before marking the job as failed.

2. **Progress Tracking** — Report progress as a percentage of completed map and
   reduce tasks.

3. **Custom Partitioner Support** — Allow users to provide their own partition
   function instead of the default hash-based one.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
