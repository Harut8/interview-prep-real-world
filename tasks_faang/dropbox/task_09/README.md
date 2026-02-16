# Task 09: File Activity Feed

## Overview
You are building a file activity feed system similar to Dropbox's activity notifications. The system tracks file and folder events, supports pagination, and provides activity feeds for users across their own and shared content.

**Time Limit: 60 minutes**

## Architecture
- `ActivityFeed` manages event recording and retrieval
- `ActivityEvent` represents a single activity (create, edit, delete, share, etc.)
- `EventType` enum defines all activity types
- `FeedPage` represents a paginated page of results
- Events are stored in-memory with cursor-based pagination

## Bugs to Fix (3)

1. **Shared Folder Activity Not Visible to All Members**: When an event occurs in a shared folder, it only appears in the feed of the file owner, not the feeds of other users the folder is shared with.

2. **Event Deduplication Too Aggressive**: The deduplication logic removes "duplicate" events by comparing type + path within a time window. However, legitimate repeated actions (e.g., editing a file twice within 5 minutes) are incorrectly filtered as duplicates.

3. **Pagination Skips Events When New Ones Arrive**: The pagination uses integer offsets. When new events are inserted at the top of the feed between page requests, the offset-based cursor causes events to be skipped or repeated.

## Features to Implement (3)

1. **Activity Filtering by Action Type**: Allow filtering the feed to show only specific event types (e.g., only edits, only shares).

2. **Activity Rollup**: Batch similar events together. For example, "Alice edited report.txt 5 times" instead of 5 separate "Alice edited report.txt" entries.

3. **Webhook Notifications**: When specified event types occur, send a notification to a registered webhook URL (simulated as a callback function).

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Activity feed implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
