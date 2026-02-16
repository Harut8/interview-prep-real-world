"""Tests for File Version Control."""

import pytest
import threading

from app import (
    VersionManager,
    VersionStore,
    FileVersion,
    FileType,
    DiffResult,
)


@pytest.fixture
def store() -> VersionStore:
    return VersionStore()


@pytest.fixture
def manager(store: VersionStore) -> VersionManager:
    return VersionManager(store)


class TestBasicVersioning:
    """Tests for basic version save and retrieval."""

    def test_save_creates_version(self, manager: VersionManager):
        """Saving a file should create a version entry."""
        version = manager.save("doc.txt", b"Hello World", author="alice")

        assert version.version_number == 1
        assert version.file_path == "doc.txt"
        assert version.author == "alice"
        assert version.size == 11

    def test_multiple_saves_increment_version(self, manager: VersionManager):
        """Each save should increment the version number."""
        v1 = manager.save("doc.txt", b"Version 1")
        v2 = manager.save("doc.txt", b"Version 2")
        v3 = manager.save("doc.txt", b"Version 3")

        assert v1.version_number == 1
        assert v2.version_number == 2
        assert v3.version_number == 3

    def test_get_history_returns_newest_first(self, manager: VersionManager):
        """Version history should be sorted newest first."""
        manager.save("doc.txt", b"V1")
        manager.save("doc.txt", b"V2")
        manager.save("doc.txt", b"V3")

        history = manager.get_history("doc.txt")

        assert len(history) == 3
        assert history[0].version_number == 3
        assert history[2].version_number == 1


class TestConcurrentVersioning:
    """Tests for concurrent version safety."""

    # FAILING: BUG #1 - Version numbers not assigned atomically
    def test_concurrent_saves_unique_version_numbers(self, manager: VersionManager):
        """Concurrent saves should each get a unique version number."""
        results: list[FileVersion] = []
        errors: list[Exception] = []

        def save_version(content: bytes):
            try:
                v = manager.save("shared.txt", content, author="user")
                results.append(v)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=save_version, args=(f"Content {i}".encode(),))
            for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        version_numbers = [v.version_number for v in results]
        assert len(set(version_numbers)) == 10, (
            f"Expected 10 unique version numbers, got {version_numbers}"
        )


class TestDiff:
    """Tests for diff computation."""

    def test_text_diff_detects_changes(self, manager: VersionManager):
        """Diff between text versions should show added/removed lines."""
        manager.save("notes.txt", b"line 1\nline 2\nline 3\n")
        manager.save("notes.txt", b"line 1\nmodified line 2\nline 3\nline 4\n")

        result = manager.diff("notes.txt", 1, 2)

        assert result.lines_added > 0
        assert result.lines_removed > 0
        assert "modified line 2" in result.unified_diff

    # FAILING: BUG #2 - Diff crashes on binary files
    def test_binary_diff_does_not_crash(self, manager: VersionManager):
        """Diff between binary versions should not raise an exception."""
        binary_v1 = bytes(range(256)) * 10
        binary_v2 = bytes(range(255, -1, -1)) * 10
        manager.save("image.png", binary_v1)
        manager.save("image.png", binary_v2)

        # Should not crash; should indicate binary diff
        result = manager.diff("image.png", 1, 2)

        assert result.is_binary is True
        assert result.file_path == "image.png"


class TestRestore:
    """Tests for version restore."""

    # FAILING: BUG #3 - Restore doesn't create a new version entry
    def test_restore_creates_new_version(self, manager: VersionManager):
        """Restoring to an old version should create a new version entry."""
        manager.save("doc.txt", b"Original content")
        manager.save("doc.txt", b"Updated content")
        manager.save("doc.txt", b"Latest content")

        # Restore to version 1
        restored = manager.restore("doc.txt", 1)

        # A new version (v4) should be created with v1's content
        history = manager.get_history("doc.txt")
        assert len(history) == 4, (
            f"Expected 4 versions after restore, got {len(history)}"
        )
        latest = history[0]
        assert latest.version_number == 4
        assert latest.content == b"Original content"

    def test_restore_nonexistent_version_raises(self, manager: VersionManager):
        """Restoring a nonexistent version should raise ValueError."""
        manager.save("doc.txt", b"Only version")

        with pytest.raises(ValueError):
            manager.restore("doc.txt", 999)


class TestVersionPruning:
    """Tests for version pruning."""

    # TODO: Implement version pruning
    def test_prune_keeps_last_n(self, manager: VersionManager):
        """Pruning should keep only the last N versions."""
        for i in range(10):
            manager.save("big.txt", f"Version {i}".encode())

        deleted_count = manager.prune_versions("big.txt", keep_last_n=3)

        assert deleted_count == 7
        remaining = manager.get_history("big.txt")
        assert len(remaining) == 3
        assert remaining[0].version_number == 10
        pytest.skip("TODO: Implement version pruning")


class TestStorageQuota:
    """Tests for storage quota tracking."""

    # TODO: Implement storage quota enforcement
    def test_total_storage_tracking(self, store: VersionStore, manager: VersionManager):
        """Store should accurately track total storage used."""
        manager.save("a.txt", b"Hello")  # 5 bytes
        manager.save("b.txt", b"World!!")  # 7 bytes

        assert store.total_storage_used() == 12

    # TODO: Implement quota enforcement
    def test_quota_enforcement(self, manager: VersionManager):
        """Saving should fail if it would exceed the storage quota."""
        pytest.skip("TODO: Implement storage quota limit enforcement")
