# Task 10: Trash & Recovery Service

## Overview
You are building a trash and recovery system similar to Dropbox's deleted files feature. Files are soft-deleted into a trash bin, can be recovered within a retention period, and are auto-purged after expiry.

**Time Limit: 60 minutes**

## Architecture
- `TrashService` manages the trash bin with soft-delete, restore, and purge operations
- `TrashedItem` represents a file in the trash with original location and expiry
- `PurgeScheduler` handles automatic cleanup of expired trash items
- `RecoveryResult` contains the outcome of a restore operation

## Bugs to Fix (3)

1. **Restoring to Deleted Folder Fails Silently**: When a file is restored, if its original parent folder has been deleted, the restore returns success but the file is not actually accessible. Should either recreate the folder or return an error.

2. **Auto-Purge Timezone Bug**: The purge scheduler compares expiry times using a mix of naive and aware datetimes. This causes items to be purged too early or too late depending on the server's timezone offset.

3. **Recovery Doesn't Restore Sharing Permissions**: When a file is recovered from trash, its original sharing permissions are lost. The file comes back as unshared even if it was previously shared with multiple users.

## Features to Implement (3)

1. **Bulk Recovery**: Implement `bulk_restore(item_ids)` that restores multiple items in a single operation, with a summary of successes and failures.

2. **Permanent Delete Confirmation**: Before permanently deleting, require a confirmation token. Generate a token with `request_permanent_delete(item_id)` and execute with `confirm_permanent_delete(item_id, token)`.

3. **Trash Storage Accounting**: Track total trash size per user. Implement `get_trash_stats(user_id)` returning item count, total size, and oldest/newest items.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Trash & recovery implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
