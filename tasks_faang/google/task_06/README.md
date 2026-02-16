# Task 06: Log Aggregator & Analyzer

**Time Limit: 60 minutes**

## Overview

You are given a log aggregation system that ingests structured log entries,
computes metrics (P95/P99 latencies, error rates), and supports filtering
and time-windowed analysis.

## Current State

The system can ingest logs, compute basic metrics, and filter by level. However,
there are bugs in timestamp parsing, percentile calculation, and level filtering.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Timestamp parsing handles only one format** — The parser only handles ISO 8601
   format but not Unix timestamps or other common formats. Logs with Unix timestamps
   fail silently and are dropped.

2. **Percentile calculation uses wrong interpolation** — The P95/P99 calculation
   doesn't correctly interpolate between values, returning the wrong percentile.

3. **Log level filtering is case-sensitive** — Filtering by level "ERROR" misses
   logs with level "error" or "Error".

## Features to Implement

1. **Log Pattern Detection** — Group similar error messages using pattern extraction
   (e.g., "Connection timeout to 10.0.0.1" and "Connection timeout to 10.0.0.2"
   should be grouped as "Connection timeout to {IP}").

2. **Alerting Rules** — Define threshold-based alerts (e.g., "alert if error rate
   exceeds 10% in a 5-minute window").

3. **Time-Windowed Aggregation** — Compute metrics over fixed time windows
   (e.g., per-minute or per-hour buckets).

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
