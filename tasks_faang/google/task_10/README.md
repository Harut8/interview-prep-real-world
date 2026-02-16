# Task 10: Data Pipeline Orchestrator

**Time Limit: 60 minutes**

## Overview

You are given a data pipeline orchestrator that defines and executes ETL
(Extract-Transform-Load) pipelines with dependencies between stages. Stages can
depend on other stages, and the orchestrator runs them in the correct order.

## Current State

The orchestrator supports defining pipelines with stages, resolving dependencies,
and executing stages. However, there are bugs in diamond dependency handling,
error propagation, and retry logic.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Diamond dependency runs task twice** — When two stages depend on a common
   upstream stage, and a downstream stage depends on both, the common upstream
   stage is executed twice instead of once (diamond pattern: A -> B, A -> C, B+C -> D).

2. **Error in one branch doesn't propagate** — When a stage fails, downstream
   stages that depend on it still execute instead of being skipped/failed.

3. **Retry doesn't reset task state** — When retrying a failed stage, the old
   error state persists and the stage is treated as already failed.

## Features to Implement

1. **Pipeline Scheduling** — Support cron-like scheduling for pipeline execution
   (e.g., "every hour", "daily at midnight").

2. **Pipeline Versioning** — Track versions of pipeline definitions and allow
   running specific versions.

3. **Execution History and Metrics** — Record execution history with timing
   metrics for each run.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
