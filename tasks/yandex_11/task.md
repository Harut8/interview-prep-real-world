# S3-Like Object Storage Client

Implement an S3-like client that uploads large files to buckets with fixed capacity, optimizing for I/O, then extend to support concurrent uploads.

## Interface

```python
class Bucket:
    def __init__(self, name: str, capacity_bytes: int) -> None: ...
    def available_space(self) -> int: ...
    def has_object(self, key: str) -> bool: ...

class StorageClient:
    def __init__(self) -> None: ...
    def create_bucket(self, name: str, capacity_bytes: int) -> Bucket: ...
    def upload(self, bucket: str, key: str, data: bytes | BinaryIO) -> str: ...
    def download(self, bucket: str, key: str) -> bytes: ...
    def delete(self, bucket: str, key: str) -> None: ...
    def list_objects(self, bucket: str, prefix: str = "") -> list[str]: ...
    def multipart_upload(self, bucket: str, key: str, source: BinaryIO, chunk_size: int = 8 * 1024 * 1024) -> str: ...
```

## Requirements

### Phase 1 — Basic single-threaded
- `create_bucket(name, capacity)` — creates a bucket with a byte-size limit.
- `upload(bucket, key, data)` — stores the object. Raises `BucketFullError` if it wouldn't fit.
- `download(bucket, key)` — returns the data. Raises `ObjectNotFoundError`.
- `delete` / `list_objects` — standard CRUD.
- Store data in memory (dict of dicts), but design the interface as if backed by disk.

### Phase 2 — Chunked upload for large files
- `multipart_upload(bucket, key, source, chunk_size)` — reads the source stream in `chunk_size` chunks. Reassembles on download.
- Chunks are stored independently so partial uploads can be detected/resumed.
- If a chunk fails, only that chunk retries (not the whole file).

### Phase 3 — Concurrent uploads
- Support multiple concurrent uploads to the same bucket (thread-safe capacity accounting).
- Support concurrent multipart chunk uploads for a single large file (thread pool, `N` chunks in flight).
- A `ConcurrentUploader` class that wraps `StorageClient` and manages a thread pool.
- Capacity reservation: reserve space before uploading chunks to avoid over-commitment.

### Phase 4 — Optimizations
- **Deduplication**: if two keys have identical content (by hash), store only one copy.
- **Read-through cache**: LRU cache for frequently downloaded objects.
- **Progress callback**: `upload(..., on_progress=callback)` reports bytes uploaded.

## Patterns Tested

Streaming I/O, chunking, thread pools, locks/semaphores for capacity, producer-consumer, content-addressable storage, caching.

## What You Should Do

1. Write tests first — especially for concurrent scenarios (race conditions on capacity).
2. Phase 1 should take ~15 min. Phases 2-3 are the core challenge (~25 min).

## Time Target: 50 minutes
