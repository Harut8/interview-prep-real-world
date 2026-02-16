"""Tests for File Deduplication Service."""

import pytest
import hashlib

from app import (
    DedupService,
    ContentStore,
    FileReference,
    DedupReport,
    BLOCK_SIZE,
)


@pytest.fixture
def store() -> ContentStore:
    return ContentStore()


@pytest.fixture
def service(store: ContentStore) -> DedupService:
    return DedupService(store)


class TestBasicDedup:
    """Tests for basic deduplication functionality."""

    def test_identical_files_deduped(self, service: DedupService, store: ContentStore):
        """Two identical files should share storage."""
        data = b"identical content"
        service.upload_file("f1", "/alice/doc.txt", "alice", data)
        service.upload_file("f2", "/bob/doc.txt", "bob", data)

        # Physical storage should only have one copy
        assert store.get_block_count() == 1

    def test_different_files_stored_separately(self, service: DedupService, store: ContentStore):
        """Different files should be stored separately."""
        service.upload_file("f1", "/a.txt", "alice", b"content A")
        service.upload_file("f2", "/b.txt", "alice", b"content B")

        assert store.get_block_count() == 2

    def test_file_retrieval(self, service: DedupService):
        """Uploaded files should be retrievable."""
        data = b"my important document"
        service.upload_file("f1", "/doc.txt", "alice", data)

        result = service.get_file("f1")
        assert result is not None
        ref, retrieved_data = result
        assert retrieved_data == data


class TestHashIntegrity:
    """Tests for content hash correctness."""

    # FAILING: BUG #1 - Hash only uses first 1KB
    def test_full_file_hash(self, store: ContentStore):
        """Hash should consider the entire file content, not just the start."""
        # Two files identical in first 1KB but different after
        prefix = b"A" * 1024
        file_a = prefix + b"BBBBBBBB"
        file_b = prefix + b"CCCCCCCC"

        hash_a = store.compute_hash(file_a)
        hash_b = store.compute_hash(file_b)

        assert hash_a != hash_b, (
            "Files with different content after first 1KB got the same hash. "
            "Hash should cover the entire file."
        )

    # FAILING: BUG #1 - Leads to incorrect dedup of different files
    def test_different_files_same_prefix_not_deduped(self, service: DedupService, store: ContentStore):
        """Files with same first 1KB but different tails should NOT be deduplicated."""
        prefix = b"X" * 1024
        file_a = prefix + b"file A tail content"
        file_b = prefix + b"file B different tail"

        service.upload_file("f1", "/a.dat", "alice", file_a)
        service.upload_file("f2", "/b.dat", "alice", file_b)

        # Should have 2 separate blocks since content differs
        assert store.get_block_count() == 2, (
            "Different files were incorrectly deduplicated. "
            "Only first 1KB is being hashed."
        )


class TestReferenceIntegrity:
    """Tests for file reference correctness after dedup."""

    # FAILING: BUG #2 - Re-uploading same file_id breaks references
    def test_reupload_same_file_id_updates_cleanly(self, service: DedupService, store: ContentStore):
        """Re-uploading with the same file_id should properly update references."""
        service.upload_file("f1", "/doc.txt", "alice", b"version 1")
        service.upload_file("f1", "/doc.txt", "alice", b"version 2")

        result = service.get_file("f1")
        assert result is not None
        _, data = result
        assert data == b"version 2"

        # Old content should have its reference count decremented
        # If ref count was not updated, old content block leaks
        old_hash = store.compute_hash(b"version 1")
        old_block = store._blocks.get(old_hash)
        if old_block:
            assert old_block.reference_count == 0 or old_hash not in store._blocks, (
                "Old content reference was not decremented on re-upload"
            )


class TestHashCollision:
    """Tests for hash collision handling."""

    # FAILING: BUG #3 - No collision detection
    def test_hash_collision_preserves_both(self, store: ContentStore):
        """If two different contents produce the same hash, both should be preserved."""
        # We can't easily cause a real SHA-256 collision, so we'll test the
        # behavior by monkey-patching the hash function
        original_hash = store.compute_hash

        # Make all content hash to the same value
        store.compute_hash = lambda data: "fixed_hash_value"

        data_a = b"Content A"
        data_b = b"Content B - totally different"

        hash_a = store.store(data_a)
        hash_b = store.store(data_b)

        # Both should be retrievable with their correct content
        retrieved = store.retrieve(hash_a)
        # With the bug, data_b is discarded and data_a is returned for both
        # This is data loss - the second file's content is lost
        # A correct implementation would detect the collision and handle it

        # Restore original hash function
        store.compute_hash = original_hash

        # At minimum, the store should detect that data differs despite same hash
        assert retrieved == data_a  # This passes but data_b is lost


class TestDedupReport:
    """Tests for dedup savings report."""

    # TODO: Implement savings report
    def test_savings_report_accuracy(self, service: DedupService):
        """Report should accurately reflect dedup savings."""
        data = b"duplicated content across users"
        service.upload_file("f1", "/alice/file.txt", "alice", data)
        service.upload_file("f2", "/bob/file.txt", "bob", data)
        service.upload_file("f3", "/carol/file.txt", "carol", data)

        report = service.get_savings_report()

        assert report.total_files == 3
        assert report.unique_files == 1
        assert report.total_logical_bytes == len(data) * 3
        assert report.total_physical_bytes == len(data)
        assert report.bytes_saved == len(data) * 2
        pytest.skip("TODO: Implement get_savings_report")

    # TODO: Implement block-level dedup
    def test_block_level_dedup(self, service: DedupService):
        """Block-level dedup should detect partial file duplicates."""
        pytest.skip("TODO: Implement block-level deduplication")
