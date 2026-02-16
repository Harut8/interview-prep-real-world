# Task 20: Notification Service — Fix Delivery Bugs & Add Templating

**Time limit: 60 minutes**

## Existing Codebase
A notification service that sends messages via multiple channels (email, SMS, push). Uses strategy pattern for channel selection.

## Problems to Fix
1. The `send` method continues to the next channel even after successful delivery (sends duplicates).
2. Failed notifications are not stored — no retry mechanism and no audit trail.
3. Template rendering uses `str.format()` which crashes on missing keys instead of using defaults.
4. Priority ordering is broken — LOW priority notifications are sent before HIGH.

## Features to Implement
1. Add a `NotificationQueue` with priority support (HIGH sends first).
2. Add Jinja2-style templating with default values for missing variables.
3. Add delivery status tracking: pending -> sending -> delivered / failed.
4. Add `get_delivery_report(notification_id)` with full attempt history.
5. Write tests for the notification pipeline.

## What We Evaluate
- Strategy pattern
- Queue/priority handling
- Template rendering
- Error handling and auditing
