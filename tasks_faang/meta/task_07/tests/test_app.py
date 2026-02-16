"""Tests for Media Upload Service."""

import threading
import pytest
from app import (
    MediaUploadService, MediaType, UploadStatus, MediaItem,
    MAGIC_BYTES,
)


# Fake JPEG content (starts with JPEG magic bytes)
FAKE_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 1000
# Fake PNG content
FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 1000
# Fake content that is NOT an image (plain text)
FAKE_TEXT = b"This is just plain text, not an image at all."


@pytest.fixture
def service() -> MediaUploadService:
    return MediaUploadService()


class TestFileSizeValidation:
    def test_valid_image_size(self, service: MediaUploadService):
        """FAILING: A 5 MB image should be accepted (limit is 10 MB).

        Bug: Size comparison uses bytes vs MB without conversion.
        """
        five_mb = 5 * 1024 * 1024  # 5,242,880 bytes
        content = b"\xff\xd8\xff\xe0" + b"\x00" * (five_mb - 4)
        result = service.upload("photo.jpg", content, "alice")
        assert isinstance(result, MediaItem), (
            f"5 MB upload should succeed, got error: {result}"
        )

    def test_oversized_image_rejected(self, service: MediaUploadService):
        """PASSING (once size bug fixed): 15 MB image should be rejected."""
        fifteen_mb = 15 * 1024 * 1024
        content = b"\xff\xd8\xff\xe0" + b"\x00" * (fifteen_mb - 4)
        result = service.upload("big.jpg", content, "alice")
        assert isinstance(result, str), "15 MB upload should fail"
        assert "too large" in result.lower()


class TestMimeDetection:
    def test_mime_from_content_not_extension(self, service: MediaUploadService):
        """FAILING: MIME type should be detected from content, not just extension.

        Bug: A text file renamed to .jpg should be rejected.
        """
        # Text content with .jpg extension
        result = service.upload("malicious.jpg", FAKE_TEXT, "alice")
        # Should be rejected because actual content is not JPEG
        assert isinstance(result, str), (
            "File with wrong content type should be rejected"
        )

    def test_valid_jpeg_detected(self, service: MediaUploadService):
        """PASSING: Valid JPEG with correct extension should be accepted."""
        result = service.upload("photo.jpg", FAKE_JPEG, "alice")
        assert isinstance(result, MediaItem)
        assert result.mime_type == "image/jpeg"


class TestAlbumOrdering:
    def test_concurrent_uploads_unique_positions(self, service: MediaUploadService):
        """FAILING: Concurrent uploads should get unique positions.

        Bug: Non-atomic position increment causes position collisions.
        """
        album = service.create_album("alice", "Vacation")
        results: list[MediaItem] = []
        errors: list[Exception] = []

        def upload_file(i: int):
            try:
                content = b"\xff\xd8\xff\xe0" + bytes([i]) * 100
                result = service.upload(
                    f"photo_{i}.jpg", content, "alice", album_id=album.album_id
                )
                if isinstance(result, MediaItem):
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=upload_file, args=(i,))
                   for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        positions = [r.position for r in results]
        assert len(set(positions)) == len(positions), (
            f"Positions should be unique, got: {sorted(positions)}"
        )

    def test_sequential_uploads_ordered(self, service: MediaUploadService):
        """PASSING: Sequential uploads should have correct ordering."""
        album = service.create_album("alice", "Trip")
        for i in range(3):
            content = b"\xff\xd8\xff\xe0" + bytes([i]) * 100
            service.upload(f"photo_{i}.jpg", content, "alice",
                           album_id=album.album_id)
        media = service.get_album_media(album.album_id)
        positions = [m.position for m in media]
        assert positions == [0, 1, 2]


class TestDuplicateDetection:
    def test_duplicate_returns_existing(self, service: MediaUploadService):
        """TODO: Uploading same content twice should return existing item."""
        result1 = service.upload_with_dedup("photo1.jpg", FAKE_JPEG, "alice")
        result2 = service.upload_with_dedup("photo1_copy.jpg", FAKE_JPEG, "alice")
        assert isinstance(result1, MediaItem)
        assert isinstance(result2, MediaItem)
        assert result1.media_id == result2.media_id, (
            "Duplicate content should return same media item"
        )

    def test_different_content_creates_new(self, service: MediaUploadService):
        """TODO: Different content should create a new item."""
        result1 = service.upload_with_dedup("photo1.jpg", FAKE_JPEG, "alice")
        result2 = service.upload_with_dedup("photo2.png", FAKE_PNG, "alice")
        assert isinstance(result1, MediaItem)
        assert isinstance(result2, MediaItem)
        assert result1.media_id != result2.media_id


class TestImageVariants:
    def test_generate_variants(self, service: MediaUploadService):
        """TODO: Should generate thumbnail, medium, large variants."""
        result = service.upload("photo.jpg", FAKE_JPEG, "alice")
        assert isinstance(result, MediaItem)
        variants = service.generate_variants(result.media_id, 2000, 1500)
        assert len(variants) == 3
        names = {v.name for v in variants}
        assert names == {"thumbnail", "medium", "large"}

    def test_variants_maintain_aspect_ratio(self, service: MediaUploadService):
        """TODO: Variants should maintain aspect ratio."""
        result = service.upload("photo.jpg", FAKE_JPEG, "alice")
        assert isinstance(result, MediaItem)
        # Original is 2000x1000 (2:1 ratio)
        variants = service.generate_variants(result.media_id, 2000, 1000)
        for v in variants:
            ratio = v.width / v.height
            assert abs(ratio - 2.0) < 0.01, (
                f"Variant {v.name} has wrong ratio: {ratio}"
            )

    def test_skip_variant_larger_than_original(self, service: MediaUploadService):
        """TODO: Should not generate variant larger than original."""
        result = service.upload("small.jpg", FAKE_JPEG, "alice")
        assert isinstance(result, MediaItem)
        # Original is only 100px wide — large (1200px) should be skipped
        variants = service.generate_variants(result.media_id, 100, 75)
        widths = [v.width for v in variants]
        assert all(w <= 100 for w in widths), (
            f"No variant should exceed original width. Got widths: {widths}"
        )
