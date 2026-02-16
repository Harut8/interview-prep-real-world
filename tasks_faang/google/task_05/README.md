# Task 05: Task DAG Executor

**Time Limit: 60 minutes**

## Overview

You are given a DAG (Directed Acyclic Graph) executor that runs dependent tasks
with support for parallel execution. Tasks declare their dependencies, and the
executor runs them in topological order, parallelizing independent tasks.

## Current State

The executor can build a DAG from task definitions, detect (some) cycles, and
execute tasks. However, there are bugs in cycle detection, result passing, and
parallelism control.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Incomplete cycle detection** — The cycle detector only checks for direct
   self-loops (A -> A) but misses longer cycles (A -> B -> C -> A).

2. **Completed task results aren't passed to dependents** — When a task completes,
   its result should be available to downstream tasks via the context, but the
   result dict is not being updated before dependents run.

3. **Max parallelism not respected** — The executor is supposed to limit concurrent
   tasks to `max_workers`, but it submits all ready tasks at once regardless.

## Features to Implement

1. **Task Retry with Backoff** — Failed tasks should be retried up to N times
   with exponential backoff between retries.

2. **Execution Timeline Visualization** — Generate a text-based Gantt chart showing
   when each task started and finished.

3. **Conditional Task Execution** — Support tasks that only execute if a condition
   function returns True (based on upstream results).

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
