"""Tests for Sharing & Permissions."""

import pytest
from datetime import datetime, timezone, timedelta

from app import (
    PermissionManager,
    Permission,
    ShareEntry,
    FileNode,
    ShareLink,
    AuditEntry,
)


@pytest.fixture
def pm() -> PermissionManager:
    return PermissionManager()


@pytest.fixture
def setup_folder_tree(pm: PermissionManager) -> PermissionManager:
    """Create a nested folder structure:
    /projects/ (owner: alice)
      /projects/docs/ (owner: alice)
        /projects/docs/specs/ (owner: alice)
          /projects/docs/specs/api.txt (owner: alice)
        /projects/docs/readme.txt (owner: alice)
      /projects/src/ (owner: alice)
        /projects/src/main.py (owner: alice)
    """
    pm.create_node("/projects/", is_folder=True, owner="alice")
    pm.create_node("/projects/docs/", is_folder=True, owner="alice")
    pm.create_node("/projects/docs/specs/", is_folder=True, owner="alice")
    pm.create_node("/projects/docs/specs/api.txt", is_folder=False, owner="alice")
    pm.create_node("/projects/docs/readme.txt", is_folder=False, owner="alice")
    pm.create_node("/projects/src/", is_folder=True, owner="alice")
    pm.create_node("/projects/src/main.py", is_folder=False, owner="alice")
    return pm


class TestBasicPermissions:
    """Basic permission grant and check."""

    def test_owner_has_owner_permission(self, pm: PermissionManager):
        """File owner should have OWNER permission."""
        pm.create_node("/myfile.txt", is_folder=False, owner="alice")

        assert pm.check_permission("/myfile.txt", "alice") == Permission.OWNER

    def test_grant_read_permission(self, pm: PermissionManager):
        """Granting READ permission should be retrievable."""
        pm.create_node("/shared.txt", is_folder=False, owner="alice")
        pm.grant_permission("/shared.txt", "bob", Permission.READ, granted_by="alice")

        assert pm.check_permission("/shared.txt", "bob") == Permission.READ

    def test_no_permission_by_default(self, pm: PermissionManager):
        """Users without grants should have NONE permission."""
        pm.create_node("/private.txt", is_folder=False, owner="alice")

        assert pm.check_permission("/private.txt", "eve") == Permission.NONE


class TestPermissionInheritance:
    """Tests for permission inheritance through folder hierarchy."""

    def test_direct_child_inherits(self, setup_folder_tree: PermissionManager):
        """Direct children should inherit parent folder permissions."""
        pm = setup_folder_tree
        pm.grant_permission("/projects/", "bob", Permission.READ, granted_by="alice")

        # Direct child should inherit
        assert pm.check_permission("/projects/docs/", "bob") >= Permission.READ

    # FAILING: BUG #1 - Deep nesting doesn't inherit permissions
    def test_deeply_nested_inherits(self, setup_folder_tree: PermissionManager):
        """Deeply nested items should inherit from any ancestor."""
        pm = setup_folder_tree
        pm.grant_permission("/projects/", "bob", Permission.READ, granted_by="alice")

        # Two levels deep - should still inherit from /projects/
        perm = pm.check_permission("/projects/docs/specs/api.txt", "bob")
        assert perm >= Permission.READ, (
            f"Expected READ or higher for deeply nested file, got {perm.name}"
        )


class TestRevokePermission:
    """Tests for permission revocation."""

    # FAILING: BUG #2 - Revoking folder share doesn't revoke sub-item shares
    def test_revoke_folder_cascades_to_subitems(self, setup_folder_tree: PermissionManager):
        """Revoking folder access should also revoke access to sub-items."""
        pm = setup_folder_tree

        # Grant access to folder AND explicitly to a sub-item
        pm.grant_permission("/projects/", "bob", Permission.WRITE, granted_by="alice")
        pm.grant_permission("/projects/docs/readme.txt", "bob", Permission.WRITE, granted_by="alice")

        # Revoke access to the entire folder
        pm.revoke_permission("/projects/", "bob", revoked_by="alice")

        # Sub-item's explicit share should also be revoked
        perm = pm.check_permission("/projects/docs/readme.txt", "bob")
        assert perm == Permission.NONE, (
            f"Expected NONE after parent revocation, got {perm.name}. "
            f"Sub-item explicit share was not revoked."
        )


class TestSymlinks:
    """Tests for symlink permission handling."""

    # FAILING: BUG #3 - Symlink uses its own permissions, not target's
    def test_symlink_uses_target_permissions(self, pm: PermissionManager):
        """Accessing a symlink should check permissions on the symlink target."""
        # Create a private file
        pm.create_node("/private/secret.txt", is_folder=False, owner="alice")

        # Create a symlink to it in a shared location
        pm.create_node(
            "/public/link_to_secret.txt",
            is_folder=False,
            owner="alice",
            symlink_target="/private/secret.txt",
        )

        # Grant bob access to /public/ but NOT /private/
        pm.create_node("/public/", is_folder=True, owner="alice")
        pm.grant_permission("/public/", "bob", Permission.READ, granted_by="alice")

        # Bob should NOT be able to access the secret file via symlink
        # because the TARGET (/private/secret.txt) is not shared with bob
        perm = pm.check_permission("/public/link_to_secret.txt", "bob")
        assert perm == Permission.NONE, (
            f"Symlink should enforce target permissions, but got {perm.name}"
        )


class TestShareLinks:
    """Tests for share link functionality."""

    # TODO: Implement share link expiry checking
    def test_share_link_creation(self, pm: PermissionManager):
        """Creating a share link should return a valid link object."""
        pm.create_node("/report.pdf", is_folder=False, owner="alice")
        link = pm.create_share_link("/report.pdf", created_by="alice", expires_in_hours=24)

        assert link.link_id is not None
        assert link.path == "/report.pdf"
        assert link.expires_at is not None

    # TODO: Implement share link expiry validation
    def test_expired_share_link_returns_none(self, pm: PermissionManager):
        """Expired share links should not grant access."""
        pytest.skip("TODO: Implement share link expiry validation in check_share_link")


class TestAuditLog:
    """Tests for permission audit logging."""

    # TODO: Implement audit logging for permission changes
    def test_grant_logged_in_audit(self, pm: PermissionManager):
        """Permission grants should be recorded in the audit log."""
        pytest.skip("TODO: Implement audit logging for grant_permission")

    # TODO: Implement ownership transfer
    def test_transfer_ownership(self, pm: PermissionManager):
        """Ownership transfer should change the owner of the file and its children."""
        pytest.skip("TODO: Implement transfer_ownership")
