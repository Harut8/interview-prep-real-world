# Task 02: Chunked File Upload

## Overview
You are building a chunked file upload system similar to Dropbox's upload API. Large files are split into fixed-size chunks, uploaded individually, and reassembled on the server. The system supports resumable uploads so that interrupted transfers can continue from where they left off.

**Time Limit: 60 minutes**

## Architecture
- `ChunkedUploader` handles splitting files and uploading chunks
- `UploadServer` receives chunks, validates them, and reassembles files
- `UploadSession` tracks the state of an in-progress upload
- `Chunk` represents an individual piece of a file with offset, data, and checksum

## Bugs to Fix (3)

1. **Off-by-One in Chunk Offset Calculation**: When splitting a file into chunks, the offset calculation has an off-by-one error that causes the last chunk to either overlap with the previous chunk or miss a byte.

2. **Resume Doesn't Verify Existing Chunks**: When resuming an upload, the system trusts that previously uploaded chunks are intact without verifying their checksums. If a chunk was corrupted during a previous upload attempt, the corruption goes undetected.

3. **Concurrent Uploads Corrupt Data**: When two upload sessions write to the same file simultaneously, chunks get interleaved and the final file is corrupted. There is no locking or conflict detection.

## Features to Implement (3)

1. **Parallel Chunk Upload**: Upload multiple chunks simultaneously using threading. Respect a configurable `max_parallel` limit.

2. **Upload Progress Tracking**: Implement a `ProgressTracker` that reports:
   - Percentage complete
   - Bytes uploaded / total bytes
   - Estimated time remaining
   - Upload speed (bytes/sec)

3. **End-to-End Checksum Verification**: After all chunks are uploaded, verify the reassembled file's checksum against the original file's checksum to ensure integrity.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Chunked upload implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
