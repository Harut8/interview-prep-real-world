"""
File Deduplication Service - Detect and deduplicate identical files.

Simulates Dropbox-style content-addressed storage with deduplication
at the file and block level.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


BLOCK_SIZE = 4 * 1024  # 4KB blocks for block-level dedup


@dataclass
class ContentBlock:
    """A block of content stored in the content-addressed store."""
    content_hash: str
    data: bytes
    size: int
    reference_count: int = 0


@dataclass
class FileReference:
    """A user-facing file that references content in the store."""
    file_id: str
    path: str
    owner_id: str
    content_hash: str
    size: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DedupReport:
    """Summary of deduplication savings."""
    total_logical_bytes: int = 0  # Sum of all file sizes
    total_physical_bytes: int = 0  # Actual storage used
    bytes_saved: int = 0
    dedup_ratio: float = 0.0
    total_files: int = 0
    unique_files: int = 0


class ContentStore:
    """
    Content-addressed storage backend.

    Stores data blocks keyed by their content hash. Identical content
    is stored only once regardless of how many files reference it.
    """

    def __init__(self):
        self._blocks: dict[str, ContentBlock] = {}

    def compute_hash(self, data: bytes) -> str:
        """
        Compute content hash for data.

        BUG #1: Only hashes the first 1024 bytes, not the full content.
        Files with identical first 1KB but different remaining content
        will produce the same hash and be incorrectly deduplicated.
        """
        # BUG #1: Should hash ALL data, but only hashes first 1KB
        return hashlib.sha256(data[:1024]).hexdigest()

    def store(self, data: bytes) -> str:
        """
        Store data and return its content hash.

        BUG #3: If a hash collision occurs (different data, same hash),
        the existing content is silently overwritten. No collision
        detection is performed.
        """
        content_hash = self.compute_hash(data)

        if content_hash in self._blocks:
            # BUG #3: Assumes hash match means content match.
            # Does NOT verify that existing data actually matches new data.
            # If this is a hash collision, the old data is kept and the
            # new data is silently discarded.
            self._blocks[content_hash].reference_count += 1
        else:
            self._blocks[content_hash] = ContentBlock(
                content_hash=content_hash,
                data=data,
                size=len(data),
                reference_count=1,
            )

        return content_hash

    def retrieve(self, content_hash: str) -> bytes | None:
        """Retrieve data by content hash."""
        block = self._blocks.get(content_hash)
        if block:
            return block.data
        return None

    def remove_reference(self, content_hash: str) -> bool:
        """Decrement reference count. Remove block if no references remain."""
        block = self._blocks.get(content_hash)
        if not block:
            return False

        block.reference_count -= 1
        if block.reference_count <= 0:
            del self._blocks[content_hash]
        return True

    def get_physical_size(self) -> int:
        """Total actual bytes stored."""
        return sum(block.size for block in self._blocks.values())

    def get_block_count(self) -> int:
        return len(self._blocks)


class DedupService:
    """
    File deduplication service.

    Manages file references and delegates storage to the content-addressed
    store, achieving deduplication transparently.
    """

    def __init__(self, content_store: ContentStore | None = None):
        self.store = content_store or ContentStore()
        # file_id -> FileReference
        self._files: dict[str, FileReference] = {}
        # owner_id -> list of file_ids
        self._user_files: dict[str, list[str]] = {}

    def upload_file(self, file_id: str, path: str, owner_id: str, data: bytes) -> FileReference:
        """
        Upload a file, deduplicating its content.

        BUG #2: When a file with the same content already exists in the store,
        the new file reference is created correctly, but if the original file
        reference is later accessed, it may point to stale data because the
        reference bookkeeping has an error.
        """
        content_hash = self.store.store(data)

        ref = FileReference(
            file_id=file_id,
            path=path,
            owner_id=owner_id,
            content_hash=content_hash,
            size=len(data),
        )

        # BUG #2: If a file with same file_id exists, we overwrite the ref
        # but don't decrement the old content's reference count.
        # This leads to orphaned references and incorrect ref counts.
        if file_id in self._files:
            old_ref = self._files[file_id]
            # Missing: self.store.remove_reference(old_ref.content_hash)
            pass

        self._files[file_id] = ref

        if owner_id not in self._user_files:
            self._user_files[owner_id] = []
        self._user_files[owner_id].append(file_id)

        return ref

    def get_file(self, file_id: str) -> tuple[FileReference, bytes] | None:
        """Retrieve a file's reference and data."""
        ref = self._files.get(file_id)
        if not ref:
            return None

        data = self.store.retrieve(ref.content_hash)
        if data is None:
            return None

        return ref, data

    def delete_file(self, file_id: str) -> bool:
        """Delete a file reference (content may persist if other refs exist)."""
        ref = self._files.get(file_id)
        if not ref:
            return False

        self.store.remove_reference(ref.content_hash)
        del self._files[file_id]

        if ref.owner_id in self._user_files:
            self._user_files[ref.owner_id] = [
                fid for fid in self._user_files[ref.owner_id] if fid != file_id
            ]

        return True

    def get_user_files(self, owner_id: str) -> list[FileReference]:
        """Get all files owned by a user."""
        file_ids = self._user_files.get(owner_id, [])
        return [self._files[fid] for fid in file_ids if fid in self._files]

    def get_savings_report(self) -> DedupReport:
        """
        Generate a deduplication savings report.

        Stub - needs implementation.
        """
        # TODO: Implement savings report
        return DedupReport()

    def find_duplicates(self, owner_id: str | None = None) -> dict[str, list[FileReference]]:
        """Find groups of files that share the same content."""
        hash_groups: dict[str, list[FileReference]] = {}

        files = self._files.values()
        if owner_id:
            file_ids = set(self._user_files.get(owner_id, []))
            files = [f for f in files if f.file_id in file_ids]

        for ref in files:
            if ref.content_hash not in hash_groups:
                hash_groups[ref.content_hash] = []
            hash_groups[ref.content_hash].append(ref)

        # Only return groups with actual duplicates
        return {h: refs for h, refs in hash_groups.items() if len(refs) > 1}
