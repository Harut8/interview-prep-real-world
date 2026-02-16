# Task 05: Driver Location Tracker

**Time Limit: 60 minutes**

## Overview

You are building Uber's driver location tracking service. This service receives real-time GPS updates from drivers and allows querying nearby drivers efficiently using geohashing. It is critical for the ride matching system.

## Current State

The tracker uses geohashing for spatial indexing but has several bugs in precision, ordering, and cleanup.

## Bugs to Fix

1. **Geohash Precision Too Low** - The geohash precision is set to 4 characters, which covers ~40km x 20km cells. For ride matching, we need precision 6 (1.2km x 0.6km) or 7. The current precision causes "nearby" queries to return drivers that are very far away.

2. **Location Updates Not Ordered by Timestamp** - When querying a driver's location history, updates are stored in a list but not sorted by timestamp. This means the "latest" location returned might actually be an older update that arrived late.

3. **Stale Locations Never Cleaned Up** - Drivers who go offline leave stale location entries. There is no TTL or cleanup mechanism, so queries return drivers who went offline hours ago.

## Features to Implement

1. **Geofencing Alerts** - Define geographic zones (circles or polygons). When a driver enters or exits a zone, emit an alert event. Track which zones each driver is currently in.

2. **Location History Trail** - Store and query the path/trail a driver took over a time period. Return as an ordered list of (lat, lon, timestamp) points.

## Technical Details

- Geohashing converts (lat, lon) into a string; nearby locations share prefixes
- Location updates arrive as (driver_id, latitude, longitude, timestamp)
- "Nearby" queries: return all drivers within a geohash cell
- Stale timeout: locations older than 5 minutes should be excluded

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
