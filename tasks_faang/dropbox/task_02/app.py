"""
Chunked File Upload - Upload large files in chunks with resume support.

Simulates Dropbox-style chunked upload with session management,
resume capability, and chunk integrity verification.
"""

from __future__ import annotations

import hashlib
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable


DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4MB


class UploadStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class Chunk:
    index: int
    offset: int
    size: int
    data: bytes
    checksum: str

    @staticmethod
    def compute_checksum(data: bytes) -> str:
        return hashlib.md5(data).hexdigest()


@dataclass
class UploadSession:
    session_id: str
    file_name: str
    file_size: int
    chunk_size: int
    total_chunks: int
    status: UploadStatus = UploadStatus.PENDING
    uploaded_chunks: dict[int, Chunk] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class UploadServer:
    """
    Server-side handler for chunked uploads.

    Manages upload sessions, receives chunks, validates integrity,
    and reassembles completed uploads.
    """

    def __init__(self):
        self.sessions: dict[str, UploadSession] = {}
        self.completed_files: dict[str, bytes] = {}
        # BUG #3: No locking mechanism for concurrent access
        # self._lock = threading.Lock()  # Should exist but doesn't

    def create_session(self, file_name: str, file_size: int, chunk_size: int = DEFAULT_CHUNK_SIZE) -> UploadSession:
        session_id = str(uuid.uuid4())
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        session = UploadSession(
            session_id=session_id,
            file_name=file_name,
            file_size=file_size,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            status=UploadStatus.IN_PROGRESS,
        )
        self.sessions[session_id] = session
        return session

    def upload_chunk(self, session_id: str, chunk: Chunk) -> bool:
        """
        Upload a single chunk to a session.

        BUG #3: No synchronization - concurrent uploads to same session
        can corrupt data due to race conditions in dict updates and
        completion checks.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Unknown session: {session_id}")

        if session.status == UploadStatus.COMPLETED:
            raise ValueError(f"Session already completed: {session_id}")

        if chunk.index >= session.total_chunks:
            raise ValueError(f"Chunk index {chunk.index} exceeds total chunks {session.total_chunks}")

        # Verify chunk checksum
        actual_checksum = Chunk.compute_checksum(chunk.data)
        if actual_checksum != chunk.checksum:
            raise ValueError(f"Chunk {chunk.index} checksum mismatch")

        # BUG #3: No lock around this critical section
        session.uploaded_chunks[chunk.index] = chunk

        # Check if upload is complete
        if len(session.uploaded_chunks) == session.total_chunks:
            self._finalize_upload(session)

        return True

    def get_session_status(self, session_id: str) -> UploadSession | None:
        return self.sessions.get(session_id)

    def get_uploaded_chunk_indices(self, session_id: str) -> list[int]:
        """
        Return indices of already-uploaded chunks for resume.

        BUG #2: Returns indices without verifying that stored chunks
        still have valid checksums. Corrupted chunks are treated as valid.
        """
        session = self.sessions.get(session_id)
        if not session:
            return []
        # Should verify checksums of stored chunks, but just returns indices
        return list(session.uploaded_chunks.keys())

    def _finalize_upload(self, session: UploadSession) -> None:
        """Reassemble chunks into final file."""
        chunks_in_order = sorted(session.uploaded_chunks.values(), key=lambda c: c.index)
        file_data = b"".join(chunk.data for chunk in chunks_in_order)
        self.completed_files[session.file_name] = file_data
        session.status = UploadStatus.COMPLETED
        session.completed_at = time.time()


class ChunkedUploader:
    """
    Client-side chunked file uploader.

    Splits files into chunks, manages upload sessions, and handles
    resume logic for interrupted uploads.
    """

    def __init__(self, server: UploadServer, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.server = server
        self.chunk_size = chunk_size

    def split_into_chunks(self, data: bytes) -> list[Chunk]:
        """
        Split file data into chunks.

        BUG #1: Off-by-one error in offset calculation. The offset for
        each chunk after the first is calculated incorrectly.
        """
        chunks: list[Chunk] = []
        total_size = len(data)

        index = 0
        offset = 0
        while offset < total_size:
            end = min(offset + self.chunk_size, total_size)
            chunk_data = data[offset:end]
            checksum = Chunk.compute_checksum(chunk_data)

            chunks.append(Chunk(
                index=index,
                offset=offset,
                size=len(chunk_data),
                data=chunk_data,
                checksum=checksum,
            ))

            # BUG #1: Off-by-one - should be offset += self.chunk_size
            # but instead advances one byte less, causing overlapping chunks
            offset += self.chunk_size - 1
            index += 1

        return chunks

    def upload(self, file_name: str, data: bytes, session_id: str | None = None) -> UploadSession:
        """Upload a file, optionally resuming an existing session."""
        chunks = self.split_into_chunks(data)

        if session_id:
            session = self.server.get_session_status(session_id)
            if not session:
                raise ValueError(f"Cannot resume: session {session_id} not found")
            already_uploaded = set(self.server.get_uploaded_chunk_indices(session_id))
        else:
            session = self.server.create_session(file_name, len(data), self.chunk_size)
            already_uploaded = set()

        for chunk in chunks:
            if chunk.index in already_uploaded:
                # BUG #2: Skips already-uploaded chunks without verifying
                # their integrity. If a chunk was corrupted, it stays corrupted.
                continue
            self.server.upload_chunk(session.session_id, chunk)

        return session

    def resume_upload(self, session_id: str, data: bytes) -> UploadSession:
        """Resume an interrupted upload."""
        return self.upload("", data, session_id=session_id)


class ProgressTracker:
    """
    Tracks upload progress.

    Stub implementation - needs to be completed.
    """

    def __init__(self, total_bytes: int):
        self.total_bytes = total_bytes
        self.bytes_uploaded = 0
        self.start_time: float | None = None

    def update(self, bytes_sent: int) -> None:
        if self.start_time is None:
            self.start_time = time.time()
        self.bytes_uploaded += bytes_sent

    @property
    def percentage(self) -> float:
        if self.total_bytes == 0:
            return 100.0
        return (self.bytes_uploaded / self.total_bytes) * 100

    @property
    def speed_bps(self) -> float:
        """Bytes per second."""
        if self.start_time is None:
            return 0.0
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.bytes_uploaded / elapsed

    @property
    def eta_seconds(self) -> float | None:
        """Estimated time remaining in seconds."""
        if self.speed_bps == 0:
            return None
        remaining = self.total_bytes - self.bytes_uploaded
        return remaining / self.speed_bps
