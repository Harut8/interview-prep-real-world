"""
Collaborative Editing Lock Manager - Manage file locks for collaborative editing.

Simulates Dropbox-style file locking with exclusive/shared locks,
expiry, queuing, and lock escalation.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional
from collections import deque


class LockType(Enum):
    READ = auto()    # Shared lock - multiple readers allowed
    WRITE = auto()   # Exclusive lock - single writer, no readers


@dataclass
class FileLock:
    """An active lock on a file."""
    lock_id: str
    file_path: str
    owner_id: str
    owner_name: str  # Display name (mutable)
    lock_type: LockType
    acquired_at: float  # time.time() timestamp
    ttl_seconds: int = 300  # 5 minutes default

    @property
    def expires_at(self) -> float:
        return self.acquired_at + self.ttl_seconds

    def is_expired(self) -> bool:
        """
        Check if the lock has expired.

        BUG #1: This method exists but is never called by the LockManager.
        Lock expiry is effectively disabled.
        """
        return time.time() > self.expires_at


@dataclass
class LockRequest:
    """A queued request for a lock."""
    request_id: str
    file_path: str
    requester_id: str
    requester_name: str
    lock_type: LockType
    requested_at: float = field(default_factory=time.time)


@dataclass
class LockAuditEntry:
    """Audit trail entry for lock operations."""
    timestamp: datetime
    file_path: str
    action: str  # "acquired", "released", "expired", "force_unlocked"
    actor_id: str
    details: str = ""


class LockManager:
    """
    Manages file locks for collaborative editing.

    Supports read (shared) and write (exclusive) locks with
    configurable TTL and lock queuing.
    """

    def __init__(self):
        # file_path -> list of active FileLock objects
        self._locks: dict[str, list[FileLock]] = {}
        # file_path -> queue of LockRequest
        self._queues: dict[str, deque[LockRequest]] = {}
        # Audit log
        self._audit_log: list[LockAuditEntry] = []
        # BUG #2: No threading lock for atomic operations
        # self._mutex = threading.Lock()

    def acquire_lock(
        self,
        file_path: str,
        owner_id: str,
        owner_name: str,
        lock_type: LockType = LockType.WRITE,
        ttl_seconds: int = 300,
    ) -> FileLock | None:
        """
        Attempt to acquire a lock on a file.

        BUG #1: Does not check if existing locks have expired before
        deciding if the file is available.

        BUG #2: The check-then-acquire is not atomic. Two threads can
        both see the file as unlocked, then both acquire a lock.

        Returns the lock if acquired, None if the file is already locked
        in a conflicting manner.
        """
        # BUG #1: Should call self._cleanup_expired(file_path) here
        # but doesn't, so expired locks still block new acquisitions.

        existing_locks = self._locks.get(file_path, [])

        # Check for conflicts
        # BUG #2: No mutex around this check + acquire sequence
        if lock_type == LockType.WRITE:
            # Write lock conflicts with any existing lock
            if existing_locks:
                return None
        else:
            # Read lock conflicts with existing write locks
            if any(lock.lock_type == LockType.WRITE for lock in existing_locks):
                return None

        # Create and store the lock
        lock = FileLock(
            lock_id=str(uuid.uuid4()),
            file_path=file_path,
            owner_id=owner_id,
            owner_name=owner_name,
            lock_type=lock_type,
            acquired_at=time.time(),
            ttl_seconds=ttl_seconds,
        )

        if file_path not in self._locks:
            self._locks[file_path] = []
        self._locks[file_path].append(lock)

        self._audit_log.append(LockAuditEntry(
            timestamp=datetime.now(timezone.utc),
            file_path=file_path,
            action="acquired",
            actor_id=owner_id,
            details=f"{lock_type.name} lock, TTL={ttl_seconds}s",
        ))

        return lock

    def release_lock(self, file_path: str, owner_name: str) -> bool:
        """
        Release a lock held by the given owner.

        BUG #3: Uses owner_name (mutable display name) instead of
        owner_id (immutable) for ownership verification. If a user
        changes their display name, they can't release their own lock.
        """
        locks = self._locks.get(file_path, [])

        for i, lock in enumerate(locks):
            # BUG #3: Compares owner_name instead of owner_id
            if lock.owner_name == owner_name:
                locks.pop(i)
                if not locks:
                    del self._locks[file_path]

                self._audit_log.append(LockAuditEntry(
                    timestamp=datetime.now(timezone.utc),
                    file_path=file_path,
                    action="released",
                    actor_id=owner_name,  # BUG #3: should be owner_id
                ))

                # Process lock queue
                self._process_queue(file_path)
                return True

        return False

    def get_lock_info(self, file_path: str) -> list[FileLock]:
        """Get all active locks on a file."""
        return list(self._locks.get(file_path, []))

    def is_locked(self, file_path: str) -> bool:
        """Check if a file has any active locks."""
        return bool(self._locks.get(file_path))

    def get_lock_owner(self, file_path: str) -> str | None:
        """Get the owner of the write lock on a file."""
        locks = self._locks.get(file_path, [])
        for lock in locks:
            if lock.lock_type == LockType.WRITE:
                return lock.owner_id
        return None

    def _cleanup_expired(self, file_path: str) -> int:
        """Remove expired locks for a file. Returns count of removed locks."""
        locks = self._locks.get(file_path, [])
        if not locks:
            return 0

        active = [lock for lock in locks if not lock.is_expired()]
        removed = len(locks) - len(active)

        if active:
            self._locks[file_path] = active
        elif file_path in self._locks:
            del self._locks[file_path]

        return removed

    def _process_queue(self, file_path: str) -> None:
        """Process the lock queue after a lock is released."""
        queue = self._queues.get(file_path)
        if not queue:
            return

        # Try to grant the next queued request
        request = queue[0]
        lock = self.acquire_lock(
            file_path=request.file_path,
            owner_id=request.requester_id,
            owner_name=request.requester_name,
            lock_type=request.lock_type,
        )
        if lock:
            queue.popleft()
            if not queue:
                del self._queues[file_path]

    def enqueue_lock_request(
        self,
        file_path: str,
        requester_id: str,
        requester_name: str,
        lock_type: LockType = LockType.WRITE,
    ) -> LockRequest:
        """Add a lock request to the queue."""
        request = LockRequest(
            request_id=str(uuid.uuid4()),
            file_path=file_path,
            requester_id=requester_id,
            requester_name=requester_name,
            lock_type=lock_type,
        )

        if file_path not in self._queues:
            self._queues[file_path] = deque()
        self._queues[file_path].append(request)

        return request

    def escalate_lock(self, file_path: str, owner_id: str) -> bool:
        """
        Escalate a READ lock to a WRITE lock.

        Stub - needs implementation.
        """
        # TODO: Implement lock escalation
        return False

    def force_unlock(self, file_path: str, admin_id: str, reason: str = "") -> bool:
        """
        Force-release all locks on a file (admin operation).

        Stub - needs implementation.
        """
        # TODO: Implement force unlock
        return False

    def get_audit_log(self, file_path: str | None = None) -> list[LockAuditEntry]:
        """Get audit log, optionally filtered by file path."""
        if file_path:
            return [e for e in self._audit_log if e.file_path == file_path]
        return list(self._audit_log)
