# Task 08: Notification Aggregator

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Notification Aggregator. It groups, batches, and delivers
notifications to users. Similar notifications are aggregated (e.g., "Alice and 5
others liked your post"), and user preferences control delivery.

## Existing Codebase

The `app.py` file contains a `NotificationAggregator` that:
- Creates notifications of various types (like, comment, share, friend_request, mention)
- Groups similar notifications together
- Buckets notifications by time periods
- Checks user notification preferences before sending

## Known Bugs (3-4 to find and fix)

1. **Aggregation groups wrong types** — The grouping key does not include
   notification type, so likes and comments on the same post get grouped together.
2. **Time bucketing crosses day boundaries** — The time bucket calculation uses
   simple hour division, causing buckets that span midnight to be split incorrectly
   or grouped across days.
3. **Notification preferences not checked** — The `send` method does not verify
   user preferences before delivering. All notifications are sent regardless of
   user settings.

## Features to Implement

1. **Notification Digests** — Combine all pending notifications for a user into
   a single digest (list of aggregated summary strings).
2. **Quiet Hours** — Users can set quiet hours (e.g., 22:00 to 07:00). Notifications
   during quiet hours are queued and delivered after.
3. **Priority Override** — High-priority notifications (e.g., security alerts)
   bypass quiet hours and are always delivered immediately.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
