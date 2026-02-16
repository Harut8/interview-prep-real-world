"""
Trash & Recovery Service - Soft-delete with recovery and auto-purge.

Simulates Dropbox-style trash bin with soft-delete, timed expiry,
recovery with sharing restoration, and auto-purge scheduling.
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Optional, Callable


DEFAULT_RETENTION_DAYS = 30


class RestoreStatus(Enum):
    SUCCESS = auto()
    ITEM_NOT_FOUND = auto()
    ITEM_EXPIRED = auto()
    PARENT_DELETED = auto()
    CONFLICT = auto()  # Another file exists at the original path


@dataclass
class SharePermission:
    """A sharing permission that was active before deletion."""
    user_id: str
    permission_level: str  # "read", "write", "admin"
    shared_by: str


@dataclass
class TrashedItem:
    """A file or folder in the trash."""
    item_id: str
    original_path: str
    owner_id: str
    size: int
    is_folder: bool
    deleted_at: datetime
    expires_at: datetime
    content: bytes = b""
    original_shares: list[SharePermission] = field(default_factory=list)
    permanently_deleted: bool = False


@dataclass
class FileSystemNode:
    """Represents an active file or folder in the filesystem."""
    path: str
    is_folder: bool
    owner_id: str
    size: int
    content: bytes = b""
    shares: list[SharePermission] = field(default_factory=list)


@dataclass
class RecoveryResult:
    """Result of a restore operation."""
    item_id: str
    status: RestoreStatus
    restored_path: Optional[str] = None
    message: str = ""


@dataclass
class TrashStats:
    """Statistics about a user's trash."""
    item_count: int = 0
    total_size: int = 0
    oldest_item: Optional[datetime] = None
    newest_item: Optional[datetime] = None


@dataclass
class BulkRecoveryResult:
    """Result of a bulk restore operation."""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[RecoveryResult] = field(default_factory=list)


class TrashService:
    """
    Manages the trash bin for soft-deleted files.

    Supports soft-delete, recovery, auto-purge, and sharing
    permission restoration.
    """

    def __init__(self, retention_days: int = DEFAULT_RETENTION_DAYS):
        self.retention_days = retention_days
        # item_id -> TrashedItem
        self._trash: dict[str, TrashedItem] = {}
        # Active filesystem: path -> FileSystemNode
        self._filesystem: dict[str, FileSystemNode] = {}
        # Permanent delete confirmation tokens: item_id -> token
        self._delete_tokens: dict[str, str] = {}

    def create_file(
        self,
        path: str,
        owner_id: str,
        content: bytes = b"",
        shares: list[SharePermission] | None = None,
    ) -> FileSystemNode:
        """Create a file in the filesystem."""
        node = FileSystemNode(
            path=path,
            is_folder=False,
            owner_id=owner_id,
            size=len(content),
            content=content,
            shares=shares or [],
        )
        self._filesystem[path] = node
        return node

    def create_folder(self, path: str, owner_id: str) -> FileSystemNode:
        """Create a folder in the filesystem."""
        node = FileSystemNode(
            path=path,
            is_folder=True,
            owner_id=owner_id,
            size=0,
        )
        self._filesystem[path] = node
        return node

    def delete_file(self, path: str) -> TrashedItem | None:
        """Soft-delete a file by moving it to trash."""
        node = self._filesystem.get(path)
        if not node:
            return None

        now = datetime.now(timezone.utc)
        item = TrashedItem(
            item_id=str(uuid.uuid4()),
            original_path=path,
            owner_id=node.owner_id,
            size=node.size,
            is_folder=node.is_folder,
            deleted_at=now,
            expires_at=now + timedelta(days=self.retention_days),
            content=node.content,
            original_shares=list(node.shares),
        )

        self._trash[item.item_id] = item
        del self._filesystem[path]

        return item

    def restore(self, item_id: str) -> RecoveryResult:
        """
        Restore a file from trash to its original location.

        BUG #1: Does not check if the parent folder still exists.
        Returns SUCCESS even if the parent folder was deleted,
        leaving the file inaccessible.

        BUG #3: Does not restore original sharing permissions.
        The file comes back unshared.
        """
        item = self._trash.get(item_id)
        if not item:
            return RecoveryResult(
                item_id=item_id,
                status=RestoreStatus.ITEM_NOT_FOUND,
                message="Item not found in trash",
            )

        if item.permanently_deleted:
            return RecoveryResult(
                item_id=item_id,
                status=RestoreStatus.ITEM_EXPIRED,
                message="Item has been permanently deleted",
            )

        # Check if item has expired
        if self._is_expired(item):
            return RecoveryResult(
                item_id=item_id,
                status=RestoreStatus.ITEM_EXPIRED,
                message="Item has expired from trash",
            )

        # Check for path conflict
        if item.original_path in self._filesystem:
            return RecoveryResult(
                item_id=item_id,
                status=RestoreStatus.CONFLICT,
                message=f"A file already exists at {item.original_path}",
            )

        # BUG #1: Does NOT check if parent folder exists.
        # If parent folder was also deleted, the file is restored
        # into a non-existent directory, making it inaccessible.
        # Should check: parent_path = get parent of item.original_path
        #   if parent_path not in self._filesystem: return PARENT_DELETED

        # BUG #3: Creates the node WITHOUT the original sharing permissions.
        # Should restore item.original_shares to the new node.
        restored_node = FileSystemNode(
            path=item.original_path,
            is_folder=item.is_folder,
            owner_id=item.owner_id,
            size=item.size,
            content=item.content,
            shares=[],  # BUG #3: Empty shares instead of item.original_shares
        )

        self._filesystem[item.original_path] = restored_node
        del self._trash[item_id]

        return RecoveryResult(
            item_id=item_id,
            status=RestoreStatus.SUCCESS,
            restored_path=item.original_path,
            message="File restored successfully",
        )

    def _is_expired(self, item: TrashedItem) -> bool:
        """
        Check if a trash item has expired.

        BUG #2: Compares aware datetime (expires_at, which has timezone)
        with a naive datetime (datetime.now() without timezone).
        This can cause incorrect expiry decisions.
        """
        # BUG #2: Uses naive datetime.now() instead of datetime.now(timezone.utc)
        # This comparison will either raise TypeError in strict mode
        # or silently compare incorrectly
        now = datetime.now()  # BUG: should be datetime.now(timezone.utc)
        try:
            return now > item.expires_at.replace(tzinfo=None)
        except Exception:
            # Fallback that strips timezone, but loses correct comparison
            return now > item.expires_at.replace(tzinfo=None)

    def auto_purge(self) -> int:
        """
        Permanently delete all expired trash items.

        BUG #2: Uses _is_expired which has timezone comparison issues.
        """
        purged = 0
        expired_ids = [
            item_id for item_id, item in self._trash.items()
            if self._is_expired(item) and not item.permanently_deleted
        ]

        for item_id in expired_ids:
            self._trash[item_id].permanently_deleted = True
            purged += 1

        return purged

    def permanent_delete(self, item_id: str) -> bool:
        """Permanently delete a trash item (no confirmation required - see TODO)."""
        item = self._trash.get(item_id)
        if not item or item.permanently_deleted:
            return False

        item.permanently_deleted = True
        return True

    def list_trash(self, owner_id: str) -> list[TrashedItem]:
        """List all non-expired, non-permanently-deleted trash items for a user."""
        items = []
        for item in self._trash.values():
            if (item.owner_id == owner_id
                    and not item.permanently_deleted
                    and not self._is_expired(item)):
                items.append(item)
        return sorted(items, key=lambda x: x.deleted_at, reverse=True)

    def get_trash_stats(self, user_id: str) -> TrashStats:
        """
        Get trash statistics for a user.

        Stub - needs implementation.
        """
        # TODO: Implement trash stats
        return TrashStats()

    def bulk_restore(self, item_ids: list[str]) -> BulkRecoveryResult:
        """
        Restore multiple items from trash.

        Stub - needs implementation.
        """
        # TODO: Implement bulk restore
        return BulkRecoveryResult(total=len(item_ids))

    def request_permanent_delete(self, item_id: str) -> str | None:
        """
        Generate a confirmation token for permanent deletion.

        Stub - needs implementation.
        """
        # TODO: Implement confirmation token generation
        return None

    def confirm_permanent_delete(self, item_id: str, token: str) -> bool:
        """
        Execute permanent deletion with confirmation token.

        Stub - needs implementation.
        """
        # TODO: Implement confirmed permanent deletion
        return False
