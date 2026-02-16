# Task 08: Ride Event Stream Processor

**Time Limit: 60 minutes**

## Overview

You are building Uber's ride event stream processor. This service ingests real-time events about rides (requested, accepted, started, completed, cancelled) and processes them to maintain ride state, compute metrics, and trigger downstream actions.

## Current State

The event processor has basic event ingestion and state machine logic, but contains bugs in event ordering, deduplication, and validation.

## Bugs to Fix

1. **Out-of-Order Events Handled Incorrectly** - Events may arrive out of order (e.g., "completed" before "started"). The processor should buffer and reorder events by their event timestamp, but currently processes them in arrival order, causing invalid state transitions.

2. **Duplicate Events Not Deduplicated** - The same event can be delivered multiple times (at-least-once delivery). The processor does not detect or skip duplicates, leading to incorrect state and double-counted metrics.

3. **Event Schema Validation Missing** - Events with missing required fields or invalid values (e.g., negative timestamps, unknown event types) are accepted without validation, causing downstream errors.

## Features to Implement

1. **Event Aggregation** - Compute real-time aggregations: rides per hour per zone, average trip duration, cancellation rate. Provide endpoints to query these metrics.

2. **Dead Letter Queue** - Events that cannot be processed (invalid, unrecoverable errors) should be routed to a dead letter queue (DLQ) instead of being silently dropped. Provide an endpoint to inspect and retry DLQ items.

## Technical Details

- Valid event types: RIDE_REQUESTED, DRIVER_ACCEPTED, RIDE_STARTED, RIDE_COMPLETED, RIDE_CANCELLED
- Valid state transitions: REQUESTED -> ACCEPTED -> STARTED -> COMPLETED (or CANCELLED at any point)
- Events have: event_id, ride_id, event_type, timestamp, metadata (dict)
- Events are idempotent on event_id

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
