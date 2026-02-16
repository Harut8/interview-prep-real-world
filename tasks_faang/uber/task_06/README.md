# Task 06: Payment Processing Pipeline

**Time Limit: 60 minutes**

## Overview

You are building Uber's payment processing service. This handles charging riders after trips, processing refunds, handling retries on payment failures, and currency conversions for international rides.

## Current State

The payment pipeline has basic charge and refund functionality but contains critical bugs that can lose money or overcharge customers.

## Bugs to Fix

1. **Double-Charge on Retry** - When a payment fails and is retried, the system creates a new charge without checking if the original actually succeeded (it might have succeeded but the response was lost). This causes double charges.

2. **Refund Amount Can Exceed Original Charge** - The refund logic does not track how much has already been refunded. Multiple partial refunds can exceed the original charge amount.

3. **Currency Conversion Race Condition** - Exchange rates are fetched and applied in a non-atomic operation. Between fetching the rate and applying it, the rate can change, causing incorrect amounts.

## Features to Implement

1. **Idempotency Keys** - Each payment request should accept an idempotency key. If the same key is seen twice, return the original result instead of processing again.

2. **Partial Refunds** - Support refunding a portion of a charge. Track refunded amount per charge and prevent total refunds from exceeding the charge.

3. **Payment Audit Log** - Log every payment operation (charge, refund, retry) with timestamp, amount, status, and any error details. Provide an endpoint to query the audit log.

## Technical Details

- Amounts are in cents (integers) to avoid floating point issues
- Supported currencies: USD, EUR, GBP, MXN
- Simulated payment gateway (in-memory, configurable failure rate)
- Refunds must reference the original charge ID

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
