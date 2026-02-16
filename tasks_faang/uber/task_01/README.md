# Task 01: Ride Matching Service

**Time Limit: 60 minutes**

## Overview

You are working on Uber's core ride matching service. This service matches riders requesting a ride with the nearest available drivers. The matching considers geographic distance, estimated time of arrival, and driver ratings.

## Current State

The service has a working skeleton but contains several bugs that are causing incorrect matches and system instability.

## Bugs to Fix

1. **Haversine Distance Formula** - The distance calculation between rider and driver locations is producing incorrect results. Some matches are clearly wrong (drivers 50km away being matched over drivers 2km away).

2. **Driver Status Not Updated Atomically** - When a driver is matched to a rider, their status should be updated atomically. Currently, two riders can be matched to the same driver in a race condition.

3. **No Timeout for Match Requests** - Match requests hang indefinitely when no drivers are available. There should be a configurable timeout (default 30 seconds).

## Features to Implement

1. **Match Scoring with ETA and Rating** - Instead of matching purely by distance, implement a composite score that weighs:
   - Distance/ETA (60% weight)
   - Driver rating (40% weight)
   - Return the top match along with the score breakdown.

2. **Surge Zone Awareness** - The system should be aware of surge pricing zones. When matching, if the rider is in a surge zone, only match with drivers who are also in or near that surge zone (within a configurable radius buffer).

## Technical Details

- All locations are (latitude, longitude) tuples
- Distances should be in kilometers
- Use in-memory data structures (no database)
- Thread safety is required for the matching logic

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
