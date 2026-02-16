"""
Sharing & Permissions - Share files/folders with granular permissions.

Simulates Dropbox-style sharing with permission inheritance,
access control, and share management.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import IntEnum
from typing import Optional


class Permission(IntEnum):
    """Permission levels, ordered by privilege."""
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    OWNER = 4


@dataclass
class ShareEntry:
    """Represents a sharing relationship."""
    share_id: str
    path: str
    user_id: str
    permission: Permission
    granted_by: str
    granted_at: datetime
    is_inherited: bool = False


@dataclass
class FileNode:
    """Represents a file or folder in the filesystem tree."""
    path: str
    is_folder: bool
    owner: str
    children: list[FileNode] = field(default_factory=list)
    symlink_target: Optional[str] = None  # If set, this is a symlink

    @property
    def name(self) -> str:
        return self.path.rstrip("/").split("/")[-1]

    @property
    def parent_path(self) -> str:
        parts = self.path.rstrip("/").rsplit("/", 1)
        if len(parts) > 1:
            return parts[0] + "/"
        return "/"


@dataclass
class ShareLink:
    """A shareable link granting access to a path."""
    link_id: str
    path: str
    permission: Permission
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class AuditEntry:
    """Record of a permission change."""
    timestamp: datetime
    action: str  # "grant", "revoke", "modify", "transfer"
    path: str
    actor: str
    target_user: str
    old_permission: Optional[Permission] = None
    new_permission: Optional[Permission] = None


class PermissionManager:
    """
    Manages file/folder sharing and permission checks.

    Handles permission inheritance through folder hierarchy,
    share link management, and access auditing.
    """

    def __init__(self):
        # path -> dict[user_id -> ShareEntry]
        self._shares: dict[str, dict[str, ShareEntry]] = {}
        # path -> FileNode
        self._nodes: dict[str, FileNode] = {}
        # link_id -> ShareLink
        self._share_links: dict[str, ShareLink] = {}
        # Audit log
        self._audit_log: list[AuditEntry] = []

    def create_node(self, path: str, is_folder: bool, owner: str, symlink_target: str | None = None) -> FileNode:
        """Register a file or folder."""
        node = FileNode(path=path, is_folder=is_folder, owner=owner, symlink_target=symlink_target)
        self._nodes[path] = node

        # Register parent-child relationships
        parent_path = node.parent_path
        if parent_path in self._nodes:
            self._nodes[parent_path].children.append(node)

        return node

    def grant_permission(self, path: str, user_id: str, permission: Permission, granted_by: str) -> ShareEntry:
        """Grant a user permission to a file or folder."""
        entry = ShareEntry(
            share_id=str(uuid.uuid4()),
            path=path,
            user_id=user_id,
            permission=permission,
            granted_by=granted_by,
            granted_at=datetime.now(timezone.utc),
        )

        if path not in self._shares:
            self._shares[path] = {}
        self._shares[path][user_id] = entry

        return entry

    def revoke_permission(self, path: str, user_id: str, revoked_by: str) -> bool:
        """
        Revoke a user's permission to a file or folder.

        BUG #2: Only revokes the explicit share on the given path.
        Does NOT cascade revocation to sub-items that have their own
        explicit shares for the same user.
        """
        if path in self._shares and user_id in self._shares[path]:
            del self._shares[path][user_id]
            if not self._shares[path]:
                del self._shares[path]
            # BUG #2: Should also revoke shares on all sub-items, but doesn't.
            # Sub-items with explicit shares for this user remain accessible.
            return True
        return False

    def check_permission(self, path: str, user_id: str) -> Permission:
        """
        Check a user's effective permission on a path.

        BUG #1: Permission inheritance only checks direct parent, not
        all ancestors. Deep nesting breaks inheritance.

        BUG #3: Symlinks are followed, but the permission check uses
        the permission on the symlink path rather than the target path.
        """
        node = self._nodes.get(path)
        if not node:
            return Permission.NONE

        # Owner always has OWNER permission
        if node.owner == user_id:
            return Permission.OWNER

        # BUG #3: If path is a symlink, we should check permission on
        # the TARGET path. Instead, we check permission on the symlink
        # path itself, which may have different (or no) restrictions.
        # The symlink_target is resolved but permissions are NOT checked on it.
        if node.symlink_target:
            # We follow the symlink for content, but check perms on symlink path
            # This is the bug: should check perms on node.symlink_target instead
            pass

        # Check direct permission
        direct = self._get_direct_permission(path, user_id)
        if direct != Permission.NONE:
            return direct

        # BUG #1: Only checks immediate parent for inherited permission.
        # Should walk up the entire path hierarchy to the root.
        parent_path = node.parent_path
        if parent_path and parent_path != path:
            parent_perm = self._get_direct_permission(parent_path, user_id)
            if parent_perm != Permission.NONE:
                return parent_perm

        return Permission.NONE

    def _get_direct_permission(self, path: str, user_id: str) -> Permission:
        """Get explicitly granted permission for a path (no inheritance)."""
        shares = self._shares.get(path, {})
        entry = shares.get(user_id)
        if entry:
            return entry.permission
        return Permission.NONE

    def list_shares(self, path: str) -> list[ShareEntry]:
        """List all shares for a path."""
        return list(self._shares.get(path, {}).values())

    def list_user_shares(self, user_id: str) -> list[ShareEntry]:
        """List all paths shared with a user."""
        result: list[ShareEntry] = []
        for path_shares in self._shares.values():
            if user_id in path_shares:
                result.append(path_shares[user_id])
        return result

    def get_accessible_paths(self, user_id: str) -> list[str]:
        """Get all paths a user can access (owned or shared)."""
        paths: list[str] = []
        for path, node in self._nodes.items():
            if self.check_permission(path, user_id) > Permission.NONE:
                paths.append(path)
        return paths

    def create_share_link(
        self,
        path: str,
        created_by: str,
        permission: Permission = Permission.READ,
        expires_in_hours: int | None = None,
    ) -> ShareLink:
        """Create a shareable link. Stub for implementation."""
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        link = ShareLink(
            link_id=str(uuid.uuid4()),
            path=path,
            permission=permission,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        self._share_links[link.link_id] = link
        return link

    def check_share_link(self, link_id: str) -> ShareLink | None:
        """Validate a share link. Returns None if expired or not found."""
        link = self._share_links.get(link_id)
        if not link:
            return None
        # TODO: Check expiry
        return link

    def transfer_ownership(self, path: str, new_owner: str, transferred_by: str) -> bool:
        """Transfer ownership of a file/folder. Stub for implementation."""
        # TODO: Implement ownership transfer
        return False

    def get_audit_log(self, path: str | None = None) -> list[AuditEntry]:
        """Get audit log, optionally filtered by path."""
        if path:
            return [e for e in self._audit_log if e.path == path]
        return list(self._audit_log)
