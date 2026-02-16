# Task 03: Trip Fare Calculator

**Time Limit: 60 minutes**

## Overview

You are building Uber's trip fare calculation service. After a trip completes, this service calculates the total fare including base fare, distance charge, time charge, surge multiplier, tolls, and tips.

## Current State

The fare calculator handles basic calculations but contains bugs related to money handling and business logic.

## Bugs to Fix

1. **Floating Point Rounding Errors** - Money calculations use raw floating point arithmetic, causing penny-level discrepancies (e.g., $10.005 rounding unpredictably). All money must be handled in cents (integers) or use proper rounding.

2. **Tip Applied Before Surge Instead of After** - Tips should be applied to the base fare AFTER surge calculation. Currently, the tip is added before the surge multiplier is applied, causing riders to be overcharged on tips.

3. **Negative Fare on Short Trips** - Very short trips (< 0.5 km, < 2 min) can produce negative fares when the minimum fare logic is missing. The system should enforce a minimum fare.

## Features to Implement

1. **Fare Breakdown Endpoint** - Create an endpoint that returns a detailed breakdown of each fare component (base, distance, time, surge, tip, tolls, total).

2. **Fare Estimation Before Trip** - Given pickup/dropoff locations and current surge, estimate the fare before the trip starts. Return a fare range (min/max).

3. **Promo Code Support** - Apply promotional discounts to fares. Promo codes can be percentage-based or fixed-amount, with a maximum discount cap.

## Technical Details

- All monetary values should be precise to the cent
- Surge multiplier applies to (base + distance + time) but NOT to tips or tolls
- Minimum fare: $5.00
- Base fare: $2.50, per-km: $1.50, per-minute: $0.25

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
