# Task 07: Rating & Review System

**Time Limit: 60 minutes**

## Overview

You are building Uber's bidirectional rating system. After each trip, both the rider and driver can rate each other (1-5 stars) and leave an optional text review. The system maintains running averages and supports review moderation.

## Current State

The rating system handles basic rating submission and average calculation, but several bugs affect accuracy and data integrity.

## Bugs to Fix

1. **Average Rating Calculation Uses Wrong Denominator** - The running average calculation divides by total_rides instead of total_ratings. A driver with 100 rides but only 80 ratings gets a deflated average (divided by 100 instead of 80).

2. **Rating Window Check Is Off** - Riders/drivers have 24 hours after a trip to submit a rating. The deadline check compares timestamps incorrectly, allowing ratings to be submitted after the window closes and rejecting ratings within the window.

3. **Rating Update Doesn't Invalidate Cache** - When a new rating is submitted, the cached average rating is not invalidated. Subsequent queries return stale average values until the cache expires naturally.

## Features to Implement

1. **Review Moderation (Profanity Filter)** - Text reviews should be checked against a list of prohibited words. If a review contains profanity, it should be flagged for moderation (not rejected outright — store it but mark as `pending_review`).

2. **Rating Trends Over Time** - Provide an endpoint that returns a driver's (or rider's) average rating over weekly or monthly periods, showing how their rating has changed over time.

## Technical Details

- Ratings: 1-5 stars (integers)
- Rating window: 24 hours after trip completion
- Cache TTL: 300 seconds for average ratings
- Both riders and drivers can be rated

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
