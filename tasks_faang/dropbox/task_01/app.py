"""
File Sync Engine - Detect and sync file changes between local and remote.

Simulates Dropbox-style bidirectional file synchronization with change detection,
conflict handling, and rename tracking.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Optional


class SyncDirection(Enum):
    UPLOAD = auto()
    DOWNLOAD = auto()
    DELETE_LOCAL = auto()
    DELETE_REMOTE = auto()
    RENAME_REMOTE = auto()
    CONFLICT = auto()


class ConflictStrategy(Enum):
    LOCAL_WINS = auto()
    REMOTE_WINS = auto()
    NEWEST_WINS = auto()
    KEEP_BOTH = auto()


@dataclass
class FileMetadata:
    path: str
    size: int
    modified_time: datetime
    content_hash: str
    is_deleted: bool = False

    def clone(self) -> FileMetadata:
        return FileMetadata(
            path=self.path,
            size=self.size,
            modified_time=self.modified_time,
            content_hash=self.content_hash,
            is_deleted=self.is_deleted,
        )


@dataclass
class SyncAction:
    direction: SyncDirection
    file_path: str
    old_path: Optional[str] = None
    metadata: Optional[FileMetadata] = None


@dataclass
class SyncReport:
    uploaded: int = 0
    downloaded: int = 0
    deleted: int = 0
    renamed: int = 0
    conflicted: int = 0
    bytes_transferred: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class FileStore:
    """Simulates a file storage system (local or remote)."""

    def __init__(self, name: str):
        self.name = name
        self.files: dict[str, FileMetadata] = {}

    def put_file(self, path: str, content: bytes, modified_time: datetime | None = None) -> FileMetadata:
        content_hash = hashlib.sha256(content).hexdigest()
        if modified_time is None:
            modified_time = datetime.now()
        meta = FileMetadata(
            path=path,
            size=len(content),
            modified_time=modified_time,
            content_hash=content_hash,
        )
        self.files[path] = meta
        return meta

    def get_file(self, path: str) -> FileMetadata | None:
        return self.files.get(path)

    def delete_file(self, path: str) -> bool:
        if path in self.files:
            del self.files[path]
            return True
        return False

    def rename_file(self, old_path: str, new_path: str) -> bool:
        if old_path in self.files:
            meta = self.files.pop(old_path)
            meta.path = new_path
            self.files[new_path] = meta
            return True
        return False

    def list_files(self) -> list[FileMetadata]:
        return list(self.files.values())


class FileSyncEngine:
    """
    Bidirectional file sync engine.

    Tracks file state between sync cycles and generates appropriate
    sync actions to keep local and remote in sync.
    """

    def __init__(
        self,
        local_store: FileStore,
        remote_store: FileStore,
        conflict_strategy: ConflictStrategy = ConflictStrategy.LOCAL_WINS,
    ):
        self.local_store = local_store
        self.remote_store = remote_store
        self.conflict_strategy = conflict_strategy
        # Snapshot of file states from last successful sync
        self._last_sync_state: dict[str, FileMetadata] = {}
        # Track deleted files to avoid re-syncing them
        self._deleted_paths: set[str] = set()

    def compute_actions(self) -> list[SyncAction]:
        """Compare local and remote stores to determine sync actions."""
        actions: list[SyncAction] = []

        local_files = {m.path: m for m in self.local_store.list_files()}
        remote_files = {m.path: m for m in self.remote_store.list_files()}
        all_paths = set(local_files.keys()) | set(remote_files.keys()) | set(self._last_sync_state.keys())

        for path in all_paths:
            local = local_files.get(path)
            remote = remote_files.get(path)
            last_state = self._last_sync_state.get(path)

            action = self._resolve_file_state(path, local, remote, last_state, local_files, remote_files)
            if action:
                actions.append(action)

        return actions

    def _resolve_file_state(
        self,
        path: str,
        local: FileMetadata | None,
        remote: FileMetadata | None,
        last_state: FileMetadata | None,
        local_files: dict[str, FileMetadata],
        remote_files: dict[str, FileMetadata],
    ) -> SyncAction | None:
        # Case 1: File exists only locally (new local file)
        if local and not remote and not last_state:
            return SyncAction(direction=SyncDirection.UPLOAD, file_path=path, metadata=local)

        # Case 2: File exists only remotely (new remote file)
        if remote and not local and not last_state:
            return SyncAction(direction=SyncDirection.DOWNLOAD, file_path=path, metadata=remote)

        # Case 3: File deleted locally (was synced before)
        if not local and remote and last_state:
            # BUG #2: We don't record the deletion, so next cycle the engine
            # won't find it in _last_sync_state and treats remote as "new"
            return SyncAction(direction=SyncDirection.DELETE_REMOTE, file_path=path)

        # Case 4: File deleted remotely (was synced before)
        if local and not remote and last_state:
            return SyncAction(direction=SyncDirection.DELETE_LOCAL, file_path=path)

        # Case 5: File exists in both - check for changes
        if local and remote:
            return self._check_for_changes(path, local, remote, last_state)

        return None

    def _check_for_changes(
        self,
        path: str,
        local: FileMetadata,
        remote: FileMetadata,
        last_state: FileMetadata | None,
    ) -> SyncAction | None:
        # BUG #1: Timezone comparison bug - local uses naive datetime,
        # remote uses UTC-aware datetime. This comparison is inconsistent.
        local_changed = last_state and local.modified_time > last_state.modified_time
        remote_changed = last_state and remote.modified_time > last_state.modified_time

        if local.content_hash == remote.content_hash:
            return None  # Files are identical

        if local_changed and remote_changed:
            return SyncAction(direction=SyncDirection.CONFLICT, file_path=path, metadata=local)

        # BUG #1 (continued): This comparison between possibly-naive and
        # possibly-aware datetimes can cause incorrect sync direction
        if local.modified_time > remote.modified_time:
            return SyncAction(direction=SyncDirection.UPLOAD, file_path=path, metadata=local)
        else:
            return SyncAction(direction=SyncDirection.DOWNLOAD, file_path=path, metadata=remote)

    def _detect_renames(
        self,
        local_files: dict[str, FileMetadata],
        remote_files: dict[str, FileMetadata],
    ) -> list[SyncAction]:
        """
        Detect file renames by comparing content hashes.

        BUG #3: This method exists but is never called from compute_actions().
        Renames are treated as delete + create instead of being detected
        as a single rename operation.
        """
        renames: list[SyncAction] = []

        # Find files that disappeared locally but have matching content hash in a new path
        for old_path, last_meta in self._last_sync_state.items():
            if old_path in local_files:
                continue  # Still exists, not renamed

            # Look for a new local file with same content hash
            for new_path, new_meta in local_files.items():
                if new_path not in self._last_sync_state and new_meta.content_hash == last_meta.content_hash:
                    renames.append(
                        SyncAction(
                            direction=SyncDirection.RENAME_REMOTE,
                            file_path=new_path,
                            old_path=old_path,
                            metadata=new_meta,
                        )
                    )
                    break

        return renames

    def execute_actions(self, actions: list[SyncAction]) -> SyncReport:
        """Execute the computed sync actions."""
        report = SyncReport()
        start_time = time.monotonic()

        for action in actions:
            try:
                self._execute_single_action(action, report)
            except Exception as e:
                report.errors.append(f"Error syncing {action.file_path}: {str(e)}")

        report.duration_seconds = time.monotonic() - start_time
        return report

    def _execute_single_action(self, action: SyncAction, report: SyncReport) -> None:
        if action.direction == SyncDirection.UPLOAD:
            if action.metadata:
                self.remote_store.files[action.file_path] = action.metadata.clone()
                report.uploaded += 1
                report.bytes_transferred += action.metadata.size

        elif action.direction == SyncDirection.DOWNLOAD:
            if action.metadata:
                self.local_store.files[action.file_path] = action.metadata.clone()
                report.downloaded += 1
                report.bytes_transferred += action.metadata.size

        elif action.direction == SyncDirection.DELETE_REMOTE:
            self.remote_store.delete_file(action.file_path)
            report.deleted += 1

        elif action.direction == SyncDirection.DELETE_LOCAL:
            self.local_store.delete_file(action.file_path)
            report.deleted += 1

        elif action.direction == SyncDirection.RENAME_REMOTE:
            if action.old_path:
                self.remote_store.rename_file(action.old_path, action.file_path)
                report.renamed += 1

        elif action.direction == SyncDirection.CONFLICT:
            report.conflicted += 1

    def sync(self) -> SyncReport:
        """Perform a full sync cycle."""
        actions = self.compute_actions()
        report = self.execute_actions(actions)
        self._update_sync_state()
        return report

    def _update_sync_state(self) -> None:
        """Snapshot current state for next sync comparison."""
        self._last_sync_state.clear()
        for meta in self.local_store.list_files():
            self._last_sync_state[meta.path] = meta.clone()
        # BUG #2 (continued): _deleted_paths is never populated during sync,
        # and _last_sync_state is rebuilt only from existing files,
        # so deleted files vanish from tracking entirely.
