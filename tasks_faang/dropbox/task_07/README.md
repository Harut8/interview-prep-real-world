# Task 07: File Deduplication Service

## Overview
You are building a file deduplication service similar to Dropbox's block-level dedup system. The service detects identical files (or blocks within files), stores only one copy of duplicated data, and maintains references so all users can still access their files.

**Time Limit: 60 minutes**

## Architecture
- `DedupService` manages deduplication across the file store
- `ContentStore` is a content-addressed storage (CAS) backend keyed by content hash
- `FileReference` maps a user-facing file path to stored content
- `DedupReport` summarizes deduplication savings

## Bugs to Fix (3)

1. **Hash Only Uses First 1KB**: The content hash is computed only from the first 1024 bytes of the file, not the entire file. Files that share the same first 1KB but differ later are incorrectly treated as duplicates.

2. **Dedup Breaks File References**: When deduplication occurs, the original file's data is removed from the content store and replaced with a reference. However, the reference update for the original file is incorrect, making the original file inaccessible.

3. **No Hash Collision Handling**: The content-addressed storage assumes hash uniqueness. When two different files produce the same hash (however unlikely), one file's content silently overwrites the other, causing data loss.

## Features to Implement (3)

1. **Cross-User Dedup with Privacy**: Deduplicate files across users without revealing file contents or names to other users. Only the storage backend should know about shared content.

2. **Dedup Savings Report**: Implement `get_savings_report()` returning total bytes stored, total logical bytes (sum of all file sizes), bytes saved, and dedup ratio.

3. **Block-Level Dedup**: Instead of whole-file dedup, split files into fixed-size blocks and deduplicate at the block level. This catches partial duplicates.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Deduplication service implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
