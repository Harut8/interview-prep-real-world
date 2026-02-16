"""Tests for Chunked File Upload."""

import pytest
import threading
import hashlib

from app import (
    ChunkedUploader,
    UploadServer,
    UploadSession,
    UploadStatus,
    Chunk,
    ProgressTracker,
)


@pytest.fixture
def server() -> UploadServer:
    return UploadServer()


@pytest.fixture
def uploader(server: UploadServer) -> ChunkedUploader:
    return ChunkedUploader(server, chunk_size=10)  # Small chunks for testing


class TestChunkSplitting:
    """Tests for splitting files into chunks."""

    def test_exact_chunk_boundary(self, uploader: ChunkedUploader):
        """File size exactly divisible by chunk size."""
        data = b"A" * 20  # 2 exact chunks of size 10
        chunks = uploader.split_into_chunks(data)

        assert len(chunks) == 2
        assert chunks[0].size == 10
        assert chunks[1].size == 10

    # FAILING: BUG #1 - Off-by-one in offset calculation causes overlap
    def test_reassembled_data_matches_original(self, uploader: ChunkedUploader):
        """Chunks should reassemble to the original data without overlap or gaps."""
        data = b"Hello, this is a test file with some content for chunking!"
        chunks = uploader.split_into_chunks(data)

        reassembled = b"".join(chunk.data for chunk in chunks)

        assert reassembled == data, (
            f"Reassembled data length {len(reassembled)} != original {len(data)}. "
            f"Got {len(chunks)} chunks."
        )

    # FAILING: BUG #1 - Off-by-one means wrong number of chunks
    def test_chunk_offsets_are_contiguous(self, uploader: ChunkedUploader):
        """Each chunk's offset should equal previous chunk's offset + size."""
        data = b"X" * 35  # Should be 4 chunks: 10+10+10+5
        chunks = uploader.split_into_chunks(data)

        for i in range(1, len(chunks)):
            expected_offset = chunks[i - 1].offset + chunks[i - 1].size
            assert chunks[i].offset == expected_offset, (
                f"Chunk {i} offset {chunks[i].offset} != expected {expected_offset}"
            )


class TestBasicUpload:
    """Tests for basic upload functionality."""

    def test_small_file_upload(self, uploader: ChunkedUploader, server: UploadServer):
        """Upload a file smaller than chunk size."""
        data = b"tiny"
        session = uploader.upload("small.txt", data)

        assert session.status == UploadStatus.COMPLETED
        assert server.completed_files.get("small.txt") == data

    def test_session_tracks_chunks(self, uploader: ChunkedUploader, server: UploadServer):
        """Upload session should track uploaded chunks."""
        data = b"A" * 10  # Exactly one chunk
        session = uploader.upload("one_chunk.txt", data)

        assert len(session.uploaded_chunks) >= 1
        assert session.status == UploadStatus.COMPLETED


class TestResumeUpload:
    """Tests for upload resume functionality."""

    # FAILING: BUG #2 - Resume doesn't verify existing chunk integrity
    def test_resume_detects_corrupted_chunks(self, server: UploadServer):
        """Resuming should re-upload chunks that were corrupted."""
        uploader = ChunkedUploader(server, chunk_size=10)
        data = b"ABCDEFGHIJ" * 3  # 30 bytes, 3 chunks

        # Start an upload and upload first chunk
        session = server.create_session("resume_test.txt", len(data), 10)
        chunks = uploader.split_into_chunks(data)

        # Upload first chunk normally
        server.upload_chunk(session.session_id, chunks[0])

        # Corrupt the stored chunk data
        stored_chunk = session.uploaded_chunks[0]
        corrupted = Chunk(
            index=0,
            offset=0,
            size=10,
            data=b"XXXXXXXXXX",  # Wrong data!
            checksum=stored_chunk.checksum,  # Old checksum (now invalid)
        )
        session.uploaded_chunks[0] = corrupted

        # Resume should detect corruption and re-upload chunk 0
        uploader.resume_upload(session.session_id, data)

        # Verify the final file is correct
        if session.session_id in server.sessions:
            final_session = server.sessions[session.session_id]
            if final_session.status == UploadStatus.COMPLETED:
                assert server.completed_files["resume_test.txt"] == data, (
                    "Resumed upload has corrupted data - chunk integrity not verified"
                )


class TestConcurrentUploads:
    """Tests for concurrent upload safety."""

    # FAILING: BUG #3 - No locking for concurrent uploads
    def test_concurrent_uploads_to_same_session(self, server: UploadServer):
        """Concurrent chunk uploads to same session should not corrupt data."""
        data = b"A" * 100
        chunk_size = 10
        session = server.create_session("concurrent.txt", len(data), chunk_size)

        errors: list[Exception] = []
        chunks: list[Chunk] = []

        for i in range(10):
            start = i * chunk_size
            chunk_data = data[start:start + chunk_size]
            chunks.append(Chunk(
                index=i,
                offset=start,
                size=chunk_size,
                data=chunk_data,
                checksum=Chunk.compute_checksum(chunk_data),
            ))

        def upload_chunk(chunk: Chunk):
            try:
                server.upload_chunk(session.session_id, chunk)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=upload_chunk, args=(c,)) for c in chunks]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent upload: {errors}"
        assert session.status == UploadStatus.COMPLETED
        assert server.completed_files.get("concurrent.txt") == data


class TestProgressTracking:
    """Tests for upload progress tracking."""

    # TODO: Integrate ProgressTracker with ChunkedUploader
    def test_progress_percentage(self):
        """Progress should report accurate completion percentage."""
        tracker = ProgressTracker(total_bytes=100)
        tracker.update(25)
        assert tracker.percentage == 25.0
        tracker.update(25)
        assert tracker.percentage == 50.0

    # TODO: Implement parallel chunk upload with progress
    def test_parallel_upload_with_progress(self, server: UploadServer):
        """Upload chunks in parallel with progress reporting."""
        pytest.skip("TODO: Implement parallel chunk upload with configurable max_parallel")

    # TODO: Implement end-to-end checksum verification
    def test_end_to_end_checksum(self, server: UploadServer):
        """After upload completes, verify whole-file checksum matches."""
        pytest.skip("TODO: Implement end-to-end checksum verification after assembly")
