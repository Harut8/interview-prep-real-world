# Task 06: Storage Quota Manager

## Overview
You are building a storage quota management system similar to Dropbox's storage accounting. The system tracks per-user storage usage, enforces quota limits, and provides storage analytics.

**Time Limit: 60 minutes**

## Architecture
- `QuotaManager` tracks storage usage per user and enforces limits
- `StorageAccount` represents a user's storage allocation and usage
- `FileRecord` tracks individual files and their ownership
- `QuotaPolicy` defines configurable quota rules and thresholds

## Bugs to Fix (3)

1. **Deleted Files in Trash Counted Toward Quota**: Files moved to trash are still counted in the user's storage usage. The quota calculation should exclude trashed files (or count them separately) so users can free space by emptying trash.

2. **Shared Files Double-Counted**: When a file is shared between users, its size is counted toward BOTH the owner's and the sharee's quota. Shared files should only count toward the owner's quota.

3. **Quota Check Races with Concurrent Uploads**: The quota check (is there enough space?) and the actual upload (deduct space) happen in separate steps. Two concurrent uploads can both pass the quota check, then both proceed, exceeding the quota.

## Features to Implement (3)

1. **Quota Warnings at Thresholds**: Emit warnings when usage reaches configurable thresholds (e.g., 80%, 90%, 95%). Track which warnings have been sent to avoid duplicates.

2. **Storage Breakdown by File Type**: Implement `get_storage_breakdown(user_id)` that returns a dict mapping file extensions to total bytes used.

3. **Quota Increase Requests**: Allow users to request a quota increase. Requests are stored and can be approved/denied by admins.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Storage quota implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
