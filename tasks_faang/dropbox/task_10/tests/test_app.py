"""Tests for Trash & Recovery Service."""

import pytest
from datetime import datetime, timezone, timedelta

from app import (
    TrashService,
    TrashedItem,
    FileSystemNode,
    SharePermission,
    RestoreStatus,
    RecoveryResult,
    TrashStats,
    BulkRecoveryResult,
)


@pytest.fixture
def service() -> TrashService:
    ts = TrashService(retention_days=30)
    # Create a folder structure
    ts.create_folder("/projects/", "alice")
    ts.create_folder("/projects/docs/", "alice")
    return ts


class TestBasicTrash:
    """Tests for basic trash operations."""

    def test_delete_moves_to_trash(self, service: TrashService):
        """Deleting a file should move it to trash, not permanently delete it."""
        service.create_file("/projects/docs/readme.txt", "alice", b"Hello")
        item = service.delete_file("/projects/docs/readme.txt")

        assert item is not None
        assert item.original_path == "/projects/docs/readme.txt"
        assert "/projects/docs/readme.txt" not in service._filesystem

    def test_restore_from_trash(self, service: TrashService):
        """Restoring should bring the file back to its original location."""
        service.create_file("/projects/docs/readme.txt", "alice", b"Hello")
        item = service.delete_file("/projects/docs/readme.txt")

        result = service.restore(item.item_id)

        assert result.status == RestoreStatus.SUCCESS
        assert "/projects/docs/readme.txt" in service._filesystem
        restored = service._filesystem["/projects/docs/readme.txt"]
        assert restored.content == b"Hello"

    def test_restore_nonexistent_item(self, service: TrashService):
        """Restoring a non-existent item should return ITEM_NOT_FOUND."""
        result = service.restore("nonexistent-id")

        assert result.status == RestoreStatus.ITEM_NOT_FOUND

    def test_restore_path_conflict(self, service: TrashService):
        """Restoring when a file exists at the original path should return CONFLICT."""
        service.create_file("/projects/docs/readme.txt", "alice", b"Version 1")
        item = service.delete_file("/projects/docs/readme.txt")

        # Create a new file at the same path
        service.create_file("/projects/docs/readme.txt", "alice", b"Version 2")

        result = service.restore(item.item_id)
        assert result.status == RestoreStatus.CONFLICT


class TestRestoreToDeletedFolder:
    """Tests for restoring files when parent folder is deleted."""

    # FAILING: BUG #1 - Restore succeeds even when parent folder is deleted
    def test_restore_fails_when_parent_deleted(self, service: TrashService):
        """Restoring a file whose parent folder was deleted should fail or recreate folder."""
        service.create_file("/projects/docs/spec.txt", "alice", b"Spec content")

        # Delete the file
        item = service.delete_file("/projects/docs/spec.txt")

        # Also delete the parent folder
        service.delete_file("/projects/docs/")

        # Restore should detect missing parent and return PARENT_DELETED
        result = service.restore(item.item_id)
        assert result.status == RestoreStatus.PARENT_DELETED, (
            f"Expected PARENT_DELETED, got {result.status.name}. "
            f"Restore silently succeeded with deleted parent folder."
        )


class TestTimezoneHandling:
    """Tests for timezone-correct expiry handling."""

    # FAILING: BUG #2 - Timezone comparison issues in expiry check
    def test_expiry_check_timezone_aware(self, service: TrashService):
        """Expiry check should correctly compare timezone-aware datetimes."""
        service.create_file("/projects/temp.txt", "alice", b"temporary")
        item = service.delete_file("/projects/temp.txt")

        # Item was just deleted with 30-day retention, should NOT be expired
        assert item is not None
        trash_item = service._trash[item.item_id]

        # The item's expires_at is timezone-aware (UTC)
        assert trash_item.expires_at.tzinfo is not None

        # Check that the item is NOT expired
        expired = service._is_expired(trash_item)
        assert expired is False, (
            "Freshly trashed item is being incorrectly reported as expired. "
            "Timezone comparison issue in _is_expired."
        )


class TestSharingPermissionRecovery:
    """Tests for sharing permission recovery on restore."""

    # FAILING: BUG #3 - Sharing permissions lost on restore
    def test_restore_preserves_sharing_permissions(self, service: TrashService):
        """Restored files should retain their original sharing permissions."""
        shares = [
            SharePermission(user_id="bob", permission_level="write", shared_by="alice"),
            SharePermission(user_id="carol", permission_level="read", shared_by="alice"),
        ]
        service.create_file(
            "/projects/docs/shared_doc.txt",
            "alice",
            b"Shared content",
            shares=shares,
        )

        # Delete and restore
        item = service.delete_file("/projects/docs/shared_doc.txt")
        result = service.restore(item.item_id)

        assert result.status == RestoreStatus.SUCCESS
        restored = service._filesystem["/projects/docs/shared_doc.txt"]

        assert len(restored.shares) == 2, (
            f"Expected 2 sharing permissions after restore, got {len(restored.shares)}. "
            f"Sharing permissions were not recovered."
        )
        share_users = {s.user_id for s in restored.shares}
        assert "bob" in share_users
        assert "carol" in share_users


class TestBulkRecovery:
    """Tests for bulk restore operations."""

    # TODO: Implement bulk restore
    def test_bulk_restore_multiple_items(self, service: TrashService):
        """Bulk restore should restore multiple items and report results."""
        service.create_file("/projects/a.txt", "alice", b"A")
        service.create_file("/projects/b.txt", "alice", b"B")
        service.create_file("/projects/c.txt", "alice", b"C")

        items = [
            service.delete_file("/projects/a.txt"),
            service.delete_file("/projects/b.txt"),
            service.delete_file("/projects/c.txt"),
        ]
        item_ids = [i.item_id for i in items if i]

        result = service.bulk_restore(item_ids)

        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0
        pytest.skip("TODO: Implement bulk_restore")


class TestTrashStats:
    """Tests for trash statistics."""

    # TODO: Implement trash stats
    def test_trash_stats_accuracy(self, service: TrashService):
        """Trash stats should accurately reflect trash contents."""
        service.create_file("/projects/big.dat", "alice", b"X" * 1000)
        service.create_file("/projects/small.txt", "alice", b"Y" * 100)

        service.delete_file("/projects/big.dat")
        service.delete_file("/projects/small.txt")

        stats = service.get_trash_stats("alice")

        assert stats.item_count == 2
        assert stats.total_size == 1100
        assert stats.oldest_item is not None
        assert stats.newest_item is not None
        pytest.skip("TODO: Implement get_trash_stats")

    # TODO: Implement permanent delete confirmation
    def test_permanent_delete_requires_confirmation(self, service: TrashService):
        """Permanent delete should require a confirmation token."""
        pytest.skip("TODO: Implement permanent delete confirmation workflow")
