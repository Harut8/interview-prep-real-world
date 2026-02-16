"""Tests for Storage Quota Manager."""

import pytest
import threading

from app import (
    QuotaManager,
    StorageAccount,
    FileRecord,
    FileStatus,
    QuotaPolicy,
    QuotaIncreaseRequest,
    QuotaRequestStatus,
)


@pytest.fixture
def manager() -> QuotaManager:
    qm = QuotaManager()
    qm.create_account("alice", quota_bytes=1000)
    qm.create_account("bob", quota_bytes=1000)
    return qm


def make_file(file_id: str, owner: str, size: int, ext: str = ".txt") -> FileRecord:
    return FileRecord(
        file_id=file_id,
        path=f"/files/{file_id}{ext}",
        owner_id=owner,
        size=size,
        extension=ext,
    )


class TestBasicQuota:
    """Basic quota tracking tests."""

    def test_usage_tracking(self, manager: QuotaManager):
        """Usage should accurately reflect file sizes."""
        manager.add_file(make_file("f1", "alice", 200))
        manager.add_file(make_file("f2", "alice", 300))

        assert manager.get_usage("alice") == 500

    def test_quota_check_allows_within_limit(self, manager: QuotaManager):
        """Uploads within quota should be allowed."""
        assert manager.check_quota("alice", 500) is True

    def test_quota_check_blocks_over_limit(self, manager: QuotaManager):
        """Uploads exceeding quota should be blocked."""
        manager.add_file(make_file("f1", "alice", 900))

        assert manager.check_quota("alice", 200) is False


class TestTrashQuota:
    """Tests for trash handling in quota calculation."""

    # FAILING: BUG #1 - Trashed files still count toward quota
    def test_trashed_files_not_counted(self, manager: QuotaManager):
        """Files in trash should not count toward storage quota."""
        manager.add_file(make_file("f1", "alice", 400))
        manager.add_file(make_file("f2", "alice", 400))

        # Trash one file
        manager.trash_file("f1")

        usage = manager.get_usage("alice")
        assert usage == 400, (
            f"Expected 400 bytes (only active file), got {usage}. "
            f"Trashed file is still being counted."
        )

    def test_permanently_deleted_not_counted(self, manager: QuotaManager):
        """Permanently deleted files should not count toward quota."""
        manager.add_file(make_file("f1", "alice", 500))
        manager.permanently_delete("f1")

        assert manager.get_usage("alice") == 0


class TestSharedFileQuota:
    """Tests for shared file quota handling."""

    # FAILING: BUG #2 - Shared files counted for both owner and sharee
    def test_shared_file_only_counts_for_owner(self, manager: QuotaManager):
        """Shared files should only count toward the owner's quota."""
        file_rec = make_file("shared1", "alice", 300)
        manager.add_file(file_rec)
        manager.share_file("shared1", "bob")

        alice_usage = manager.get_usage("alice")
        bob_usage = manager.get_usage("bob")

        assert alice_usage == 300, f"Owner usage should be 300, got {alice_usage}"
        assert bob_usage == 0, (
            f"Sharee usage should be 0 (shared files don't count), got {bob_usage}"
        )


class TestConcurrentQuota:
    """Tests for concurrent upload quota safety."""

    # FAILING: BUG #3 - Race condition in quota check + upload
    def test_concurrent_uploads_respect_quota(self, manager: QuotaManager):
        """Concurrent uploads should not exceed quota."""
        # Alice has 1000 bytes quota. Two uploads of 600 each should not both succeed.
        results: list[bool] = []
        errors: list[Exception] = []

        def upload(file_id: str):
            try:
                result = manager.add_file(make_file(file_id, "alice", 600))
                results.append(result)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=upload, args=("concurrent1",))
        t2 = threading.Thread(target=upload, args=("concurrent2",))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0
        # Only one upload should succeed (600 + 600 > 1000)
        successful = sum(1 for r in results if r)
        assert successful <= 1, (
            f"Expected at most 1 successful upload, got {successful}. "
            f"Quota race condition allowed both uploads."
        )


class TestQuotaWarnings:
    """Tests for quota threshold warnings."""

    def test_warning_at_threshold(self, manager: QuotaManager):
        """Warnings should trigger when usage crosses thresholds."""
        warnings_received: list[tuple[str, int]] = []

        policy = QuotaPolicy(
            warning_thresholds=[80, 90],
            on_warning=lambda uid, thresh, pct: warnings_received.append((uid, thresh)),
        )
        qm = QuotaManager(policy=policy)
        qm.create_account("charlie", quota_bytes=100)

        qm.add_file(make_file("f1", "charlie", 85, ext=".txt"))

        assert len(warnings_received) >= 1
        assert any(w[1] == 80 for w in warnings_received)


class TestStorageBreakdown:
    """Tests for storage breakdown by file type."""

    # TODO: Implement storage breakdown
    def test_breakdown_by_extension(self, manager: QuotaManager):
        """Breakdown should show bytes used per file extension."""
        manager.add_file(make_file("doc1", "alice", 100, ext=".txt"))
        manager.add_file(make_file("doc2", "alice", 200, ext=".txt"))
        manager.add_file(make_file("img1", "alice", 500, ext=".png"))

        breakdown = manager.get_storage_breakdown("alice")

        assert breakdown.get(".txt") == 300
        assert breakdown.get(".png") == 500
        pytest.skip("TODO: Implement get_storage_breakdown")

    # TODO: Implement quota increase request workflow
    def test_quota_increase_request(self, manager: QuotaManager):
        """Users should be able to request quota increases."""
        req = manager.request_quota_increase("alice", 500, "Need more space")
        assert req.status == QuotaRequestStatus.PENDING

        manager.approve_quota_increase(req.request_id, approved_by="admin")
        account = manager.get_account("alice")
        assert account is not None
        assert account.quota_bytes == 1500
