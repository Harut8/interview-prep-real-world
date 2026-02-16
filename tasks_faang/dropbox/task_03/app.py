"""
File Version Control - Track file versions with diff and restore.

Simulates Dropbox-style version history with version tracking,
diff computation, and version restore capabilities.
"""

from __future__ import annotations

import difflib
import hashlib
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional


class FileType(Enum):
    TEXT = auto()
    BINARY = auto()


@dataclass
class FileVersion:
    file_path: str
    version_number: int
    content: bytes
    content_hash: str
    size: int
    created_at: datetime
    author: str = "system"
    message: str = ""
    file_type: FileType = FileType.TEXT
    branch: str = "main"

    @staticmethod
    def compute_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()


@dataclass
class DiffResult:
    file_path: str
    version_a: int
    version_b: int
    is_binary: bool
    unified_diff: str
    lines_added: int = 0
    lines_removed: int = 0


class VersionStore:
    """
    In-memory storage for file versions.

    Stores all versions of all files keyed by (file_path, version_number).
    """

    def __init__(self):
        # file_path -> list of FileVersion sorted by version_number
        self._versions: dict[str, list[FileVersion]] = {}
        # file_path -> current latest version number
        self._current_version: dict[str, int] = {}
        # No lock for concurrent access
        self._lock = threading.Lock()

    def get_next_version_number(self, file_path: str) -> int:
        """
        Get the next version number for a file.

        BUG #1: This reads the current version, but doesn't atomically
        increment it. Two concurrent callers can get the same number.
        """
        current = self._current_version.get(file_path, 0)
        next_version = current + 1
        # BUG #1: The update happens here, but between reading and writing
        # another thread could also read the same 'current' value.
        # The lock is NOT used around the read+write pair.
        self._current_version[file_path] = next_version
        return next_version

    def save_version(self, version: FileVersion) -> None:
        if version.file_path not in self._versions:
            self._versions[version.file_path] = []
        self._versions[version.file_path].append(version)

    def get_version(self, file_path: str, version_number: int) -> FileVersion | None:
        versions = self._versions.get(file_path, [])
        for v in versions:
            if v.version_number == version_number:
                return v
        return None

    def get_latest_version(self, file_path: str) -> FileVersion | None:
        versions = self._versions.get(file_path, [])
        if not versions:
            return None
        return max(versions, key=lambda v: v.version_number)

    def get_all_versions(self, file_path: str) -> list[FileVersion]:
        return list(self._versions.get(file_path, []))

    def get_all_files(self) -> list[str]:
        return list(self._versions.keys())

    def delete_version(self, file_path: str, version_number: int) -> bool:
        versions = self._versions.get(file_path, [])
        for i, v in enumerate(versions):
            if v.version_number == version_number:
                versions.pop(i)
                return True
        return False

    def total_storage_used(self) -> int:
        """Calculate total bytes stored across all versions."""
        total = 0
        for versions in self._versions.values():
            for v in versions:
                total += v.size
        return total


class VersionManager:
    """
    High-level version management operations.

    Provides save, diff, restore, and version listing capabilities.
    """

    def __init__(self, store: VersionStore | None = None):
        self.store = store or VersionStore()

    def save(
        self,
        file_path: str,
        content: bytes,
        author: str = "system",
        message: str = "",
    ) -> FileVersion:
        """
        Save a new version of a file.

        BUG #1: Version number assignment is not atomic. Under concurrent
        save operations, two versions can receive the same version number.
        """
        # BUG #1: get_next_version_number is not protected by a lock
        version_number = self.store.get_next_version_number(file_path)

        file_type = self._detect_file_type(content)
        content_hash = FileVersion.compute_hash(content)

        version = FileVersion(
            file_path=file_path,
            version_number=version_number,
            content=content,
            content_hash=content_hash,
            size=len(content),
            created_at=datetime.now(timezone.utc),
            author=author,
            message=message,
            file_type=file_type,
        )

        self.store.save_version(version)
        return version

    def diff(self, file_path: str, version_a: int, version_b: int) -> DiffResult:
        """
        Compute diff between two versions.

        BUG #2: Assumes content is always UTF-8 text. Binary files
        cause UnicodeDecodeError or produce meaningless diff output.
        """
        va = self.store.get_version(file_path, version_a)
        vb = self.store.get_version(file_path, version_b)

        if not va or not vb:
            raise ValueError(f"Version not found: {file_path} v{version_a} or v{version_b}")

        # BUG #2: No check for binary content - directly decode as text
        text_a = va.content.decode("utf-8").splitlines(keepends=True)
        text_b = vb.content.decode("utf-8").splitlines(keepends=True)

        diff_lines = list(difflib.unified_diff(
            text_a,
            text_b,
            fromfile=f"{file_path} (v{version_a})",
            tofile=f"{file_path} (v{version_b})",
        ))

        lines_added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
        lines_removed = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

        return DiffResult(
            file_path=file_path,
            version_a=version_a,
            version_b=version_b,
            is_binary=False,
            unified_diff="".join(diff_lines),
            lines_added=lines_added,
            lines_removed=lines_removed,
        )

    def restore(self, file_path: str, version_number: int) -> FileVersion:
        """
        Restore a file to a previous version.

        BUG #3: Restoring replaces the file content but doesn't create
        a new version entry. The restore action is invisible in the
        version history.
        """
        target_version = self.store.get_version(file_path, version_number)
        if not target_version:
            raise ValueError(f"Version {version_number} not found for {file_path}")

        # BUG #3: Just returns the old version without creating a new
        # version entry. The caller has no record that a restore happened.
        # Should create a new version with the old content.
        return target_version

    def get_history(self, file_path: str) -> list[FileVersion]:
        """Get all versions of a file, newest first."""
        versions = self.store.get_all_versions(file_path)
        return sorted(versions, key=lambda v: v.version_number, reverse=True)

    def _detect_file_type(self, content: bytes) -> FileType:
        """Detect if content is text or binary."""
        try:
            content.decode("utf-8")
            return FileType.TEXT
        except UnicodeDecodeError:
            return FileType.BINARY

    def prune_versions(self, file_path: str, keep_last_n: int) -> int:
        """
        Delete old versions, keeping only the last N.

        Stub - needs implementation.
        Returns the number of versions deleted.
        """
        # TODO: Implement version pruning
        return 0
