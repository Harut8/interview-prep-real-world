# Task 07: Media Upload Service

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Media Upload Service. It handles image/video uploads with
validation, processing pipelines, album management, and duplicate detection.

## Existing Codebase

The `app.py` file contains a `MediaUploadService` that:
- Accepts file uploads with metadata (size, MIME type, name)
- Validates file size and type
- Organizes uploads into albums with ordering
- Processes uploaded media through a pipeline

## Known Bugs (3-4 to find and fix)

1. **File size validation in wrong units** — The max file size check compares
   bytes directly against a MB limit. A 5 MB file (5,242,880 bytes) is rejected
   because the code compares `5242880 > 10` instead of converting to MB first.
2. **MIME type detection uses extension only** — The MIME type is determined solely
   from the filename extension, ignoring actual file content (magic bytes). A
   malicious file with a `.jpg` extension but non-image content passes validation.
3. **Concurrent uploads corrupt album ordering** — When multiple uploads happen
   simultaneously to the same album, the position/order values collide and
   overwrite each other.

## Features to Implement

1. **Image Resizing Pipeline** — Generate thumbnail (150px), medium (600px), and
   large (1200px) representations of uploaded images. Store the resize metadata.
2. **Upload Progress Tracking** — Track upload status (pending, processing,
   complete, failed) and allow querying progress.
3. **Duplicate Detection** — Detect duplicate uploads using content hash (SHA-256).
   Return existing media item instead of creating a duplicate.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
