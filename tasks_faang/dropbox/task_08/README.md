# Task 08: Collaborative Editing Lock Manager

## Overview
You are building a file lock manager for collaborative editing, similar to Dropbox's file locking feature. The system manages exclusive and shared locks on files, handles lock expiry, and supports a waiting queue for contested locks.

**Time Limit: 60 minutes**

## Architecture
- `LockManager` manages all file locks and lock queues
- `FileLock` represents an active lock on a file
- `LockType` enum defines lock types (READ/SHARED, WRITE/EXCLUSIVE)
- `LockRequest` represents a queued request for a lock

## Bugs to Fix (3)

1. **Locks Never Expire**: The lock has a `ttl_seconds` field and an `acquired_at` timestamp, but the expiry is never checked. Once acquired, a lock persists forever even if the holder disconnects, blocking all other users.

2. **Lock Acquisition Not Atomic**: The check for "is the file locked?" and the "acquire lock" steps are separate. Two concurrent requests can both see the file as unlocked, then both acquire locks, violating mutual exclusion.

3. **Lock Owner Check Uses Username Instead of User ID**: The lock owner is verified by comparing username strings. When a user changes their display name, they lose access to their own locks. Should use immutable user IDs.

## Features to Implement (3)

1. **Lock Queue**: When a lock is contested, instead of failing immediately, add the request to a FIFO queue. When the current lock is released, the next queued request automatically acquires the lock.

2. **Lock Escalation**: Allow upgrading a READ lock to a WRITE lock without releasing and re-acquiring (which would risk losing the lock to another user).

3. **Force-Unlock by Admin**: Admins should be able to forcefully release any lock, with a reason logged for audit purposes.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Lock manager implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
