"""Tests for Collaborative Editing Lock Manager."""

import pytest
import threading
import time

from app import (
    LockManager,
    FileLock,
    LockType,
    LockRequest,
    LockAuditEntry,
)


@pytest.fixture
def lm() -> LockManager:
    return LockManager()


class TestBasicLocking:
    """Tests for basic lock acquisition and release."""

    def test_acquire_write_lock(self, lm: LockManager):
        """Should be able to acquire a write lock on an unlocked file."""
        lock = lm.acquire_lock("/doc.txt", "user1", "Alice", LockType.WRITE)

        assert lock is not None
        assert lock.lock_type == LockType.WRITE
        assert lock.owner_id == "user1"

    def test_write_lock_blocks_second_write(self, lm: LockManager):
        """Second write lock on same file should be rejected."""
        lm.acquire_lock("/doc.txt", "user1", "Alice", LockType.WRITE)
        second = lm.acquire_lock("/doc.txt", "user2", "Bob", LockType.WRITE)

        assert second is None

    def test_multiple_read_locks_allowed(self, lm: LockManager):
        """Multiple read locks on the same file should be allowed."""
        lock1 = lm.acquire_lock("/doc.txt", "user1", "Alice", LockType.READ)
        lock2 = lm.acquire_lock("/doc.txt", "user2", "Bob", LockType.READ)

        assert lock1 is not None
        assert lock2 is not None

    def test_release_allows_new_lock(self, lm: LockManager):
        """After releasing a lock, another user should be able to lock."""
        lm.acquire_lock("/doc.txt", "user1", "Alice", LockType.WRITE)
        lm.release_lock("/doc.txt", "Alice")

        lock = lm.acquire_lock("/doc.txt", "user2", "Bob", LockType.WRITE)
        assert lock is not None


class TestLockExpiry:
    """Tests for lock expiry behavior."""

    # FAILING: BUG #1 - Expired locks are never cleaned up
    def test_expired_lock_allows_new_acquisition(self, lm: LockManager):
        """An expired lock should not block new lock acquisition."""
        # Acquire a lock with very short TTL
        lock = lm.acquire_lock("/doc.txt", "user1", "Alice", LockType.WRITE, ttl_seconds=1)
        assert lock is not None

        # Wait for the lock to expire
        time.sleep(1.5)

        # Should be able to acquire a new lock since the old one expired
        new_lock = lm.acquire_lock("/doc.txt", "user2", "Bob", LockType.WRITE)
        assert new_lock is not None, (
            "Could not acquire lock after previous lock expired. "
            "Lock expiry is not being checked."
        )


class TestConcurrentLocking:
    """Tests for concurrent lock safety."""

    # FAILING: BUG #2 - Lock acquisition is not atomic
    def test_concurrent_write_locks_mutual_exclusion(self, lm: LockManager):
        """Only one of concurrent write lock attempts should succeed."""
        results: list[FileLock | None] = []
        errors: list[Exception] = []

        def try_lock(user_id: str, name: str):
            try:
                lock = lm.acquire_lock("/shared.txt", user_id, name, LockType.WRITE)
                results.append(lock)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=try_lock, args=(f"user{i}", f"User{i}"))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        successful = [r for r in results if r is not None]
        assert len(successful) == 1, (
            f"Expected exactly 1 successful write lock, got {len(successful)}. "
            f"Lock acquisition is not atomic."
        )


class TestOwnerVerification:
    """Tests for lock owner verification."""

    # FAILING: BUG #3 - Uses username instead of user ID
    def test_release_by_user_id_after_name_change(self, lm: LockManager):
        """User should be able to release their lock even after changing display name."""
        lm.acquire_lock("/doc.txt", "user1", "Alice", LockType.WRITE)

        # User changes their display name from "Alice" to "Alice Smith"
        # They should still be able to release using their user_id
        # BUG: release_lock uses owner_name, so "Alice Smith" won't match "Alice"
        released = lm.release_lock("/doc.txt", "user1")

        assert released is True, (
            "Could not release lock using user_id. "
            "Lock owner check should use user_id, not username."
        )


class TestLockQueue:
    """Tests for lock queuing."""

    def test_enqueue_and_grant_on_release(self, lm: LockManager):
        """Queued request should be granted when the current lock is released."""
        # Alice locks the file
        lm.acquire_lock("/doc.txt", "user1", "Alice", LockType.WRITE)

        # Bob queues a lock request
        request = lm.enqueue_lock_request("/doc.txt", "user2", "Bob", LockType.WRITE)
        assert request is not None

        # Alice releases
        lm.release_lock("/doc.txt", "Alice")

        # Bob should now have the lock
        locks = lm.get_lock_info("/doc.txt")
        assert len(locks) == 1
        assert locks[0].owner_id == "user2"

    # TODO: Implement lock escalation
    def test_lock_escalation_read_to_write(self, lm: LockManager):
        """A user with a READ lock should be able to escalate to WRITE."""
        pytest.skip("TODO: Implement lock escalation (READ -> WRITE)")

    # TODO: Implement force unlock by admin
    def test_force_unlock_by_admin(self, lm: LockManager):
        """Admin should be able to force-unlock any file."""
        pytest.skip("TODO: Implement force_unlock by admin")
