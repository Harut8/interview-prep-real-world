"""Tests for File Sync Engine."""

import pytest
from datetime import datetime, timezone, timedelta

from app import (
    FileSyncEngine,
    FileStore,
    FileMetadata,
    SyncAction,
    SyncDirection,
    SyncReport,
    ConflictStrategy,
)


@pytest.fixture
def local_store() -> FileStore:
    return FileStore("local")


@pytest.fixture
def remote_store() -> FileStore:
    return FileStore("remote")


@pytest.fixture
def engine(local_store: FileStore, remote_store: FileStore) -> FileSyncEngine:
    return FileSyncEngine(local_store, remote_store)


class TestBasicSync:
    """Basic sync operations that should work correctly."""

    def test_new_local_file_uploaded_to_remote(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """New local files should be uploaded to remote."""
        local_store.put_file("docs/readme.txt", b"Hello World")

        actions = engine.compute_actions()

        assert len(actions) == 1
        assert actions[0].direction == SyncDirection.UPLOAD
        assert actions[0].file_path == "docs/readme.txt"

    def test_new_remote_file_downloaded_to_local(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """New remote files should be downloaded to local."""
        remote_store.put_file("photos/cat.jpg", b"\x89PNG...", datetime.now(timezone.utc))

        actions = engine.compute_actions()

        assert len(actions) == 1
        assert actions[0].direction == SyncDirection.DOWNLOAD
        assert actions[0].file_path == "photos/cat.jpg"

    def test_identical_files_no_action(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """Files with same content hash should produce no sync actions."""
        content = b"same content"
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        local_store.put_file("shared.txt", content, now)
        remote_store.put_file("shared.txt", content, now)

        actions = engine.compute_actions()

        assert len(actions) == 0


class TestTimezoneHandling:
    """Tests for timezone-related sync behavior."""

    # FAILING: BUG #1 - Timezone comparison is inconsistent
    def test_timezone_aware_comparison(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """Modification times should be compared correctly regardless of timezone representation."""
        # Local file with naive datetime (simulating local filesystem)
        local_time = datetime(2024, 1, 15, 12, 0, 0)  # naive, local time
        local_store.put_file("report.pdf", b"local version", local_time)

        # Remote file with UTC-aware datetime (simulating server response)
        # Same actual moment in time, just different representation
        remote_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        remote_store.put_file("report.pdf", b"remote version", remote_time)

        # After initial sync, both should be tracked
        engine.sync()

        # Now update only local
        local_store.put_file("report.pdf", b"updated local", datetime(2024, 1, 15, 13, 0, 0))

        actions = engine.compute_actions()

        # Should upload since local is newer
        upload_actions = [a for a in actions if a.direction == SyncDirection.UPLOAD]
        assert len(upload_actions) == 1


class TestDeleteHandling:
    """Tests for file deletion sync behavior."""

    # FAILING: BUG #2 - Deleted files reappear after second sync
    def test_deleted_file_stays_deleted_after_multiple_syncs(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """A file deleted locally should not reappear from remote on subsequent syncs."""
        # Setup: file exists on both sides
        content = b"to be deleted"
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        local_store.put_file("old_file.txt", content, now)
        remote_store.put_file("old_file.txt", content, now)
        engine.sync()

        # Delete locally
        local_store.delete_file("old_file.txt")

        # First sync should delete from remote
        report = engine.sync()
        assert "old_file.txt" not in remote_store.files

        # Second sync should NOT re-download the file
        report2 = engine.sync()
        assert "old_file.txt" not in local_store.files, (
            "Deleted file was re-downloaded from remote!"
        )
        assert "old_file.txt" not in remote_store.files


class TestRenameDetection:
    """Tests for rename detection."""

    # FAILING: BUG #3 - Renames are not detected, treated as delete + create
    def test_rename_detected_instead_of_delete_create(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """Renaming a file locally should be detected as a rename, not delete+create."""
        content = b"important document"
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        local_store.put_file("draft.txt", content, now)
        remote_store.put_file("draft.txt", content, now)
        engine.sync()

        # Simulate local rename: delete old, create new with same content
        local_store.delete_file("draft.txt")
        local_store.put_file("final.txt", content, datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc))

        actions = engine.compute_actions()

        # Should detect rename instead of separate delete + upload
        rename_actions = [a for a in actions if a.direction == SyncDirection.RENAME_REMOTE]
        assert len(rename_actions) == 1, (
            f"Expected 1 rename action, got actions: {[(a.direction, a.file_path) for a in actions]}"
        )
        assert rename_actions[0].old_path == "draft.txt"
        assert rename_actions[0].file_path == "final.txt"


class TestConflictResolution:
    """Tests for conflict resolution strategies."""

    # TODO: Implement conflict resolution - LOCAL_WINS strategy
    def test_conflict_local_wins(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """When LOCAL_WINS is set, local version should overwrite remote on conflict."""
        engine.conflict_strategy = ConflictStrategy.LOCAL_WINS

        content = b"original"
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        local_store.put_file("conflict.txt", content, now)
        remote_store.put_file("conflict.txt", content, now)
        engine.sync()

        # Both sides modify
        local_store.put_file("conflict.txt", b"local edit", datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc))
        remote_store.put_file("conflict.txt", b"remote edit", datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc))

        report = engine.sync()

        # Local should win - remote should have local's content hash
        local_meta = local_store.get_file("conflict.txt")
        remote_meta = remote_store.get_file("conflict.txt")
        assert local_meta is not None and remote_meta is not None
        assert remote_meta.content_hash == local_meta.content_hash
        pytest.skip("TODO: Implement LOCAL_WINS conflict resolution strategy")

    # TODO: Implement conflict resolution - KEEP_BOTH strategy
    def test_conflict_keep_both(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """When KEEP_BOTH is set, conflicting file should be saved with a suffix."""
        engine.conflict_strategy = ConflictStrategy.KEEP_BOTH
        pytest.skip("TODO: Implement KEEP_BOTH conflict resolution strategy")


class TestSyncReporting:
    """Tests for sync status reporting."""

    # TODO: Implement comprehensive sync status reporting
    def test_sync_report_counts(
        self, engine: FileSyncEngine, local_store: FileStore, remote_store: FileStore
    ):
        """Sync report should accurately count all operations."""
        local_store.put_file("new_local.txt", b"upload me", datetime.now(timezone.utc))
        remote_store.put_file("new_remote.txt", b"download me", datetime.now(timezone.utc))

        report = engine.sync()

        assert report.uploaded == 1
        assert report.downloaded == 1
        assert report.bytes_transferred > 0
        assert report.duration_seconds >= 0
