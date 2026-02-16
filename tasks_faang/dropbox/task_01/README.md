# Task 01: File Sync Engine

## Overview
You are working on a file synchronization engine similar to Dropbox's core sync functionality. The engine detects changes between a local directory and a remote file store, then synchronizes them bidirectionally.

**Time Limit: 60 minutes**

## Architecture
- `FileSyncEngine` manages synchronization between local and remote file stores
- `FileMetadata` tracks file state (path, size, modification time, content hash)
- `SyncAction` represents operations to perform (upload, download, delete)
- Files are tracked via an in-memory metadata store simulating a remote server

## Bugs to Fix (3)

1. **Timezone Bug in Modification Time Comparison**: The sync engine compares modification times between local and remote, but one uses UTC timestamps while the other uses local time. This causes files to be unnecessarily re-synced or sync decisions to be wrong.

2. **Deleted Files Re-uploaded on Next Sync**: When a file is deleted locally, the engine correctly detects the deletion and removes it from remote. However, on the next sync cycle, the remote deletion record is lost, so the engine sees the remote file as "new" and downloads it again.

3. **Rename Detection Failure**: When a file is renamed, the engine treats it as a delete of the old file plus creation of a new file. This means renamed files are re-uploaded entirely instead of performing a server-side rename, wasting bandwidth.

## Features to Implement (2)

1. **Conflict Resolution Strategies**: When both local and remote versions of a file have changed since last sync, implement configurable strategies:
   - `LOCAL_WINS`: Keep local version
   - `REMOTE_WINS`: Keep remote version
   - `NEWEST_WINS`: Keep whichever has the newer modification time
   - `KEEP_BOTH`: Rename the conflicting file with a suffix

2. **Sync Status Reporting**: Implement a `get_sync_status()` method that returns a `SyncReport` with:
   - Number of files uploaded, downloaded, deleted, renamed, conflicted
   - Total bytes transferred
   - List of errors encountered
   - Sync duration

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Main sync engine implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
