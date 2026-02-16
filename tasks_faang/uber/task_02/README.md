# Task 02: Surge Pricing Calculator

**Time Limit: 60 minutes**

## Overview

You are building Uber's surge pricing engine. This service dynamically adjusts pricing based on the ratio of ride demand to driver supply in geographic zones. When demand exceeds supply, prices increase to incentivize more drivers to come online.

## Current State

The surge calculator has basic zone management and multiplier calculation, but contains critical bugs affecting pricing accuracy.

## Bugs to Fix

1. **Division by Zero** - When a zone has zero available drivers, the demand/supply ratio calculation crashes with a `ZeroDivisionError`. This should result in maximum surge, not an error.

2. **Price Multiplier Has No Cap** - The surge multiplier can grow unboundedly. In production, this led to a $14,000 ride. There should be a configurable maximum multiplier (default 5.0x).

3. **Zone Boundary Overlap** - When checking which zone a location falls in, overlapping zone boundaries cause a location to be assigned to the wrong zone (it always picks the last matching zone instead of the most specific one).

## Features to Implement

1. **Price Smoothing Over Time** - Surge multipliers should not jump instantly. Implement exponential smoothing so the multiplier transitions gradually (smoothing factor alpha = 0.3). New = alpha * calculated + (1 - alpha) * previous.

2. **Historical Pricing Query** - Add an endpoint to query historical surge multipliers for a zone over a time range. Store multiplier history with timestamps.

## Technical Details

- Zones are defined as circular regions (center point + radius in km)
- Surge multiplier = demand_count / supply_count (with adjustments)
- Base fare should never be modified, only the multiplier returned
- All prices in USD

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
