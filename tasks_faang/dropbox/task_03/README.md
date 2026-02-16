# Task 03: File Version Control

## Overview
You are building a file version control system similar to Dropbox's version history feature. Every time a file is modified, a new version is created. Users can view diffs between versions, restore old versions, and manage version history.

**Time Limit: 60 minutes**

## Architecture
- `VersionStore` manages all file versions in memory
- `FileVersion` represents a single version with metadata and content
- `VersionManager` provides high-level operations (save, diff, restore)
- `DiffResult` represents differences between two versions

## Bugs to Fix (3)

1. **Non-Atomic Version Number Increment**: The version number is read, incremented, and stored in separate steps. Under concurrent access, two saves can get the same version number, causing one version to be silently overwritten.

2. **Diff Fails on Binary Files**: The diff algorithm assumes all content is UTF-8 text. When encountering binary files, it crashes or produces garbage output instead of gracefully indicating that binary files differ.

3. **Restore Doesn't Create New Version**: Restoring a file to an old version overwrites the current state but doesn't create a new version entry. This means the restore action itself isn't tracked in history, and there's no way to undo a restore.

## Features to Implement (3)

1. **Version Branching**: Allow creating named branches from any version. Saving a new version can target a specific branch.

2. **Storage Quota Tracking**: Track total storage used across all versions of all files. Enforce a configurable quota limit.

3. **Version Pruning**: Implement `prune_versions(file_path, keep_last_n)` to delete old versions while retaining the most recent N versions.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Version control implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
