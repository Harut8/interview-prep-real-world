# Task 04: Sharing & Permissions

## Overview
You are building a file sharing and permissions system similar to Dropbox's sharing model. Users can share files and folders with others using granular permission levels. Permissions on folders should cascade to their contents.

**Time Limit: 60 minutes**

## Architecture
- `PermissionManager` manages access control for files and folders
- `ShareEntry` represents a sharing relationship (who has what access to what)
- `Permission` enum defines access levels (NONE, READ, WRITE, ADMIN, OWNER)
- `FileNode` represents files and folders in a tree structure
- Paths use forward slashes and folder paths end with `/`

## Bugs to Fix (3)

1. **Nested Folder Permission Inheritance Broken**: When a folder is shared, its subfolders and files should inherit that permission. Currently, only the direct children inherit; deeper nested items do not get the inherited permission.

2. **Removing Share Doesn't Revoke Sub-items**: When share access is removed from a folder, explicit shares on sub-items within that folder are not revoked. Users retain access to nested items even after the parent share is removed.

3. **Permission Check Traverses Symlinks Incorrectly**: When checking permissions for a symlinked path, the system follows the symlink but uses the symlink's permissions instead of the target's permissions, allowing permission bypass via symlink creation.

## Features to Implement (3)

1. **Share Links with Expiry**: Create shareable links with configurable expiry time. Links should grant READ access to anyone with the link, and should stop working after expiry.

2. **Permission Audit Log**: Track all permission changes (grant, revoke, modify) with timestamps and the acting user. Provide `get_audit_log(path)` method.

3. **Transfer Ownership**: Implement `transfer_ownership(path, new_owner)` that transfers ownership of a file/folder and all its contents to a different user.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Sharing & permissions implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
