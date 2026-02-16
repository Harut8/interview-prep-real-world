# Task 09: Promo Code Service

**Time Limit: 60 minutes**

## Overview

You are building Uber's promotional code service. This manages promo codes with various rules (percentage off, fixed amount, expiration dates, usage limits, user eligibility) and applies them to ride fares.

## Current State

The promo code system has basic creation and application logic but contains bugs that allow abuse and incorrect discounts.

## Bugs to Fix

1. **Expired Promos Can Still Be Applied** - The expiration check compares dates incorrectly, allowing promos past their expiration date to still be used.

2. **Usage Limit Not Enforced Atomically** - The usage count check and increment are not atomic. Under concurrent usage, a promo with a limit of 100 could be used 105+ times because multiple requests pass the check before any increment.

3. **Percentage Discount Calculated on Wrong Base** - Percentage promos should apply to the fare BEFORE tips and tolls. Currently, the percentage is applied to the total including tips and tolls, giving a larger discount than intended.

## Features to Implement

1. **Stackable Promos** - Allow certain promos to be stacked (applied together). Non-stackable promos cannot be combined. When stacking, apply percentage promos first, then fixed-amount promos.

2. **First-Ride-Only Restriction** - Some promos should only work for a user's first ride ever. Validate against ride history.

3. **Promo Analytics** - Track promo usage statistics: total uses, total discount given, most popular promos, usage over time. Expose via an analytics endpoint.

## Technical Details

- Promo types: PERCENTAGE, FIXED_AMOUNT
- All monetary amounts in cents
- Promos have: code, type, value, max_discount, expiration, usage_limit
- Apply to fare (before tip/tolls) unless specified otherwise

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
