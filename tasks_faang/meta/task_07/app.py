"""
Media Upload Service
Handle image/video uploads with processing pipeline and duplicate detection.
"""

from __future__ import annotations

import hashlib
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MediaType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    UNKNOWN = "unknown"


class UploadStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


# Magic bytes signatures for common formats
MAGIC_BYTES: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"\x00\x00\x00\x1cftyp": "video/mp4",
    b"\x00\x00\x00\x20ftyp": "video/mp4",
    b"\x1aE\xdf\xa3": "video/webm",
}

EXTENSION_MIME_MAP: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
}

ALLOWED_MIME_TYPES: set[str] = {
    "image/jpeg", "image/png", "image/gif",
    "video/mp4", "video/webm", "video/quicktime",
}


@dataclass
class ImageVariant:
    name: str  # "thumbnail", "medium", "large"
    width: int
    height: int  # computed from aspect ratio
    size_bytes: int


@dataclass
class MediaItem:
    media_id: str
    filename: str
    mime_type: str
    media_type: MediaType
    size_bytes: int
    content_hash: str  # SHA-256 of content
    uploaded_by: str
    uploaded_at: float
    status: UploadStatus = UploadStatus.PENDING
    album_id: Optional[str] = None
    position: int = 0  # position within album
    variants: list[ImageVariant] = field(default_factory=list)


@dataclass
class Album:
    album_id: str
    owner_id: str
    name: str
    media_ids: list[str] = field(default_factory=list)
    _next_position: int = 0


class MediaUploadService:
    """Handles media uploads with validation, albums, and processing."""

    MAX_FILE_SIZE_MB = 10  # 10 MB max
    MAX_VIDEO_SIZE_MB = 100  # 100 MB max

    RESIZE_TARGETS = [
        ("thumbnail", 150),
        ("medium", 600),
        ("large", 1200),
    ]

    def __init__(self) -> None:
        self.media_items: dict[str, MediaItem] = {}
        self.albums: dict[str, Album] = {}
        self.hash_index: dict[str, str] = {}  # content_hash -> media_id
        self._lock = threading.Lock()

    def _detect_mime_type(self, filename: str, content: bytes) -> str:
        """Detect MIME type of uploaded file.

        BUG: Only uses filename extension, ignores magic bytes from content.
        This allows malicious files with wrong extensions to pass.
        """
        # BUG: Only checks extension, completely ignores content bytes
        ext = ""
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[1].lower()
        return EXTENSION_MIME_MAP.get(ext, "application/octet-stream")

    def _validate_file_size(self, size_bytes: int, media_type: MediaType) -> bool:
        """Validate file size against limits.

        BUG: Compares raw bytes against MB limit without conversion.
        5 MB = 5,242,880 bytes, but code checks `5242880 > 10` which is True,
        so valid files are rejected.
        """
        max_size = (self.MAX_VIDEO_SIZE_MB if media_type == MediaType.VIDEO
                    else self.MAX_FILE_SIZE_MB)
        # BUG: size_bytes is in bytes, max_size is in MB — no conversion!
        return size_bytes <= max_size

    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()

    def _classify_media(self, mime_type: str) -> MediaType:
        if mime_type.startswith("image/"):
            return MediaType.IMAGE
        if mime_type.startswith("video/"):
            return MediaType.VIDEO
        return MediaType.UNKNOWN

    def create_album(self, owner_id: str, name: str) -> Album:
        album_id = str(uuid.uuid4())
        album = Album(album_id=album_id, owner_id=owner_id, name=name)
        self.albums[album_id] = album
        return album

    def upload(self, filename: str, content: bytes, uploaded_by: str,
               album_id: str | None = None) -> MediaItem | str:
        """Upload a media file.

        Returns MediaItem on success, or error string on failure.
        """
        mime_type = self._detect_mime_type(filename, content)
        if mime_type not in ALLOWED_MIME_TYPES:
            return f"Unsupported file type: {mime_type}"

        media_type = self._classify_media(mime_type)
        if not self._validate_file_size(len(content), media_type):
            return f"File too large: {len(content)} bytes exceeds limit"

        content_hash = self._compute_hash(content)

        media_id = str(uuid.uuid4())
        position = 0

        if album_id and album_id in self.albums:
            album = self.albums[album_id]
            # BUG: Non-atomic position increment — concurrent uploads get same position
            position = album._next_position
            album._next_position += 1
            album.media_ids.append(media_id)

        item = MediaItem(
            media_id=media_id,
            filename=filename,
            mime_type=mime_type,
            media_type=media_type,
            size_bytes=len(content),
            content_hash=content_hash,
            uploaded_by=uploaded_by,
            uploaded_at=time.time(),
            album_id=album_id,
            position=position,
        )
        self.media_items[media_id] = item
        item.status = UploadStatus.COMPLETE
        return item

    def upload_with_dedup(self, filename: str, content: bytes,
                          uploaded_by: str) -> MediaItem | str:
        """Upload with duplicate detection via content hash.

        If duplicate found, return existing item instead of uploading.

        TODO: Implement duplicate detection.
        """
        return self.upload(filename, content, uploaded_by)

    def generate_variants(self, media_id: str, original_width: int,
                          original_height: int) -> list[ImageVariant]:
        """Generate image resize variants (thumbnail, medium, large).

        Only generates variants smaller than the original.
        Maintains aspect ratio.

        TODO: Implement variant generation.
        """
        return []

    def get_upload_status(self, media_id: str) -> UploadStatus | None:
        """Get upload status for a media item.

        TODO: Implement progress tracking.
        """
        item = self.media_items.get(media_id)
        if item:
            return item.status
        return None

    def get_album_media(self, album_id: str) -> list[MediaItem]:
        """Get all media in an album, ordered by position."""
        if album_id not in self.albums:
            return []
        album = self.albums[album_id]
        items = [self.media_items[mid] for mid in album.media_ids
                 if mid in self.media_items]
        items.sort(key=lambda x: x.position)
        return items
