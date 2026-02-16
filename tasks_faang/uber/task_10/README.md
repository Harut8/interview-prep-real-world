# Task 10: Fleet Analytics Dashboard API

**Time Limit: 60 minutes**

## Overview

You are building Uber's fleet analytics API. This powers the operations dashboard, providing metrics on fleet utilization, peak hours, driver performance, and trip trends. Operations teams use this to make decisions about driver incentives and capacity planning.

## Current State

The analytics service computes basic metrics but contains bugs in statistical calculations, timezone handling, and boundary conditions.

## Bugs to Fix

1. **Moving Average Calculation Uses Wrong Window** - The moving average for daily trips uses a window that is off by one: for a 7-day moving average, it only considers 6 days of data. The slicing range excludes the first element.

2. **Peak Hours Detection Has Timezone Bug** - Peak hour analysis operates on UTC timestamps but reports them as local times without conversion. A "peak hour" shown as 2 PM is actually 2 PM UTC, not the city's local time.

3. **Utilization Percentage Can Exceed 100%** - Fleet utilization (busy drivers / total drivers) can report >100% because the busy count includes drivers who are "busy" but went offline (their status was never reset). The total only counts currently online drivers.

## Features to Implement

1. **Percentile Calculations** - Compute percentile metrics (p50, p90, p95, p99) for trip duration, fare amount, and wait time. Implement using the nearest-rank method.

2. **Comparative Analytics (Week Over Week)** - Compare this week's metrics to last week's. Show absolute change and percentage change for key metrics (trips, revenue, utilization).

3. **CSV Export** - Add an endpoint that returns analytics data as a CSV file for download.

## Technical Details

- All timestamps stored as UTC epoch seconds
- Timezone offsets provided per city (e.g., "US/Pacific" = UTC-8)
- Utilization = (busy_drivers / online_drivers) * 100
- Moving average window: configurable, default 7 days

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
