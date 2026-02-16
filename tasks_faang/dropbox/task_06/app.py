"""
Storage Quota Manager - Track and enforce per-user storage quotas.

Simulates Dropbox-style storage accounting with per-user quotas,
usage tracking, and storage analytics.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional, Callable


DEFAULT_QUOTA = 2 * 1024 * 1024 * 1024  # 2GB


class FileStatus(Enum):
    ACTIVE = auto()
    TRASHED = auto()
    PERMANENTLY_DELETED = auto()


class QuotaRequestStatus(Enum):
    PENDING = auto()
    APPROVED = auto()
    DENIED = auto()


@dataclass
class FileRecord:
    """Tracks a file's storage accounting information."""
    file_id: str
    path: str
    owner_id: str
    size: int
    extension: str
    status: FileStatus = FileStatus.ACTIVE
    shared_with: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StorageAccount:
    """A user's storage quota account."""
    user_id: str
    quota_bytes: int = DEFAULT_QUOTA
    warnings_sent: set[int] = field(default_factory=set)  # threshold percentages


@dataclass
class QuotaIncreaseRequest:
    """A request for additional storage."""
    request_id: str
    user_id: str
    requested_bytes: int
    reason: str
    status: QuotaRequestStatus = QuotaRequestStatus.PENDING
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class QuotaPolicy:
    """Configurable quota policy."""
    warning_thresholds: list[int] = field(default_factory=lambda: [80, 90, 95])
    on_warning: Optional[Callable[[str, int, int], None]] = None  # user_id, threshold, usage_pct


class QuotaManager:
    """
    Manages per-user storage quotas.

    Tracks file ownership and sizes, enforces upload limits,
    and provides storage usage analytics.
    """

    def __init__(self, policy: QuotaPolicy | None = None):
        self._accounts: dict[str, StorageAccount] = {}
        self._files: dict[str, FileRecord] = {}
        self._policy = policy or QuotaPolicy()
        self._increase_requests: list[QuotaIncreaseRequest] = []
        # BUG #3: No lock for concurrent quota operations
        # self._lock = threading.Lock()

    def create_account(self, user_id: str, quota_bytes: int = DEFAULT_QUOTA) -> StorageAccount:
        """Create a storage account for a user."""
        account = StorageAccount(user_id=user_id, quota_bytes=quota_bytes)
        self._accounts[user_id] = account
        return account

    def get_account(self, user_id: str) -> StorageAccount | None:
        return self._accounts.get(user_id)

    def get_usage(self, user_id: str) -> int:
        """
        Calculate current storage usage for a user.

        BUG #1: Counts files with status=TRASHED toward usage.
        Trashed files should not count against the user's quota.

        BUG #2: Counts shared files toward BOTH the owner's
        and each sharee's usage. Shared files should only count
        toward the owner.
        """
        total = 0
        for file_record in self._files.values():
            # BUG #1: Includes TRASHED files in usage calculation
            # Should skip files where status == FileStatus.TRASHED
            if file_record.status == FileStatus.PERMANENTLY_DELETED:
                continue

            # BUG #2: Counts file for owner AND each sharee
            if file_record.owner_id == user_id:
                total += file_record.size
            elif user_id in file_record.shared_with:
                # BUG #2: Shared files shouldn't count toward sharee's quota
                total += file_record.size

        return total

    def check_quota(self, user_id: str, additional_bytes: int) -> bool:
        """
        Check if a user has enough quota for additional storage.

        BUG #3: This check is not atomic with the actual upload.
        Two concurrent calls can both pass, then both upload,
        exceeding the quota.
        """
        account = self._accounts.get(user_id)
        if not account:
            return False

        current_usage = self.get_usage(user_id)
        return (current_usage + additional_bytes) <= account.quota_bytes

    def add_file(self, file_record: FileRecord) -> bool:
        """
        Add a file to storage, checking quota first.

        BUG #3: Race condition - check and add are not atomic.
        """
        # BUG #3: No locking around check + add
        if not self.check_quota(file_record.owner_id, file_record.size):
            return False

        # Simulate some processing time that widens the race window
        self._files[file_record.file_id] = file_record

        # Check and send warnings
        self._check_warnings(file_record.owner_id)

        return True

    def trash_file(self, file_id: str) -> bool:
        """Move a file to trash."""
        record = self._files.get(file_id)
        if not record:
            return False
        record.status = FileStatus.TRASHED
        return True

    def restore_file(self, file_id: str) -> bool:
        """Restore a file from trash."""
        record = self._files.get(file_id)
        if not record or record.status != FileStatus.TRASHED:
            return False
        record.status = FileStatus.ACTIVE
        return True

    def permanently_delete(self, file_id: str) -> bool:
        """Permanently delete a file."""
        record = self._files.get(file_id)
        if not record:
            return False
        record.status = FileStatus.PERMANENTLY_DELETED
        return True

    def share_file(self, file_id: str, user_id: str) -> bool:
        """Share a file with another user."""
        record = self._files.get(file_id)
        if not record:
            return False
        if user_id not in record.shared_with:
            record.shared_with.append(user_id)
        return True

    def get_usage_percentage(self, user_id: str) -> float:
        """Get usage as a percentage of quota."""
        account = self._accounts.get(user_id)
        if not account or account.quota_bytes == 0:
            return 0.0
        return (self.get_usage(user_id) / account.quota_bytes) * 100

    def _check_warnings(self, user_id: str) -> list[int]:
        """Check if usage has crossed warning thresholds."""
        account = self._accounts.get(user_id)
        if not account:
            return []

        usage_pct = self.get_usage_percentage(user_id)
        triggered: list[int] = []

        for threshold in self._policy.warning_thresholds:
            if usage_pct >= threshold and threshold not in account.warnings_sent:
                account.warnings_sent.add(threshold)
                triggered.append(threshold)
                if self._policy.on_warning:
                    self._policy.on_warning(user_id, threshold, int(usage_pct))

        return triggered

    def get_storage_breakdown(self, user_id: str) -> dict[str, int]:
        """
        Get storage usage broken down by file extension.

        Stub - needs implementation.
        """
        # TODO: Implement storage breakdown by file type
        return {}

    def request_quota_increase(
        self,
        user_id: str,
        additional_bytes: int,
        reason: str,
    ) -> QuotaIncreaseRequest:
        """Submit a request for more storage."""
        import uuid
        request = QuotaIncreaseRequest(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            requested_bytes=additional_bytes,
            reason=reason,
        )
        self._increase_requests.append(request)
        return request

    def approve_quota_increase(self, request_id: str, approved_by: str) -> bool:
        """Approve a quota increase request."""
        for req in self._increase_requests:
            if req.request_id == request_id and req.status == QuotaRequestStatus.PENDING:
                req.status = QuotaRequestStatus.APPROVED
                req.resolved_at = datetime.now(timezone.utc)
                req.resolved_by = approved_by

                account = self._accounts.get(req.user_id)
                if account:
                    account.quota_bytes += req.requested_bytes
                return True
        return False
