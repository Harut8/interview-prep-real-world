import io
import pytest
import threading
from app import StorageClient, ConcurrentUploader, BucketFullError, ObjectNotFoundError, BucketNotFoundError


@pytest.fixture
def client():
    c = StorageClient()
    c.create_bucket("test-bucket", capacity_bytes=1024 * 1024)  # 1 MB
    return c


# --- Phase 1: Basic CRUD ---

class TestBasicCRUD:
    def test_upload_and_download(self, client):
        data = b"hello world"
        client.upload("test-bucket", "greeting.txt", data)
        assert client.download("test-bucket", "greeting.txt") == data

    def test_delete(self, client):
        client.upload("test-bucket", "file.txt", b"data")
        client.delete("test-bucket", "file.txt")
        with pytest.raises(ObjectNotFoundError):
            client.download("test-bucket", "file.txt")

    def test_list_objects(self, client):
        client.upload("test-bucket", "a.txt", b"a")
        client.upload("test-bucket", "b.txt", b"b")
        client.upload("test-bucket", "dir/c.txt", b"c")
        assert set(client.list_objects("test-bucket")) == {"a.txt", "b.txt", "dir/c.txt"}

    def test_list_with_prefix(self, client):
        client.upload("test-bucket", "logs/a.log", b"a")
        client.upload("test-bucket", "logs/b.log", b"b")
        client.upload("test-bucket", "data/c.csv", b"c")
        assert set(client.list_objects("test-bucket", prefix="logs/")) == {"logs/a.log", "logs/b.log"}

    def test_bucket_full(self, client):
        small_bucket = StorageClient()
        small_bucket.create_bucket("tiny", capacity_bytes=10)
        with pytest.raises(BucketFullError):
            small_bucket.upload("tiny", "big.bin", b"x" * 20)

    def test_download_missing(self, client):
        with pytest.raises(ObjectNotFoundError):
            client.download("test-bucket", "nope.txt")

    def test_invalid_bucket(self, client):
        with pytest.raises(BucketNotFoundError):
            client.upload("no-such-bucket", "f.txt", b"data")

    def test_overwrite(self, client):
        client.upload("test-bucket", "f.txt", b"v1")
        client.upload("test-bucket", "f.txt", b"v2")
        assert client.download("test-bucket", "f.txt") == b"v2"


# --- Phase 2: Multipart upload ---

class TestMultipartUpload:
    def test_small_file(self, client):
        source = io.BytesIO(b"small data")
        client.multipart_upload("test-bucket", "small.bin", source, chunk_size=1024)
        assert client.download("test-bucket", "small.bin") == b"small data"

    def test_large_file_chunked(self, client):
        data = b"A" * 10000
        source = io.BytesIO(data)
        client.multipart_upload("test-bucket", "big.bin", source, chunk_size=1000)
        assert client.download("test-bucket", "big.bin") == data

    def test_exact_chunk_boundary(self, client):
        data = b"B" * 3000
        source = io.BytesIO(data)
        client.multipart_upload("test-bucket", "exact.bin", source, chunk_size=1000)
        assert client.download("test-bucket", "exact.bin") == data


# --- Phase 3: Concurrent uploads ---

class TestConcurrentUploads:
    def test_concurrent_different_keys(self, client):
        uploader = ConcurrentUploader(client, max_workers=4)
        errors = []

        def upload_one(key, data):
            try:
                source = io.BytesIO(data)
                uploader.upload("test-bucket", key, source, chunk_size=100)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            t = threading.Thread(target=upload_one, args=(f"file_{i}.bin", f"data_{i}".encode() * 100))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        for i in range(10):
            result = client.download("test-bucket", f"file_{i}.bin")
            assert result == f"data_{i}".encode() * 100

    def test_capacity_respected_under_concurrency(self):
        c = StorageClient()
        c.create_bucket("small", capacity_bytes=500)
        uploader = ConcurrentUploader(c, max_workers=4)
        results = {"success": 0, "full": 0}
        lock = threading.Lock()

        def try_upload(key, data):
            try:
                source = io.BytesIO(data)
                uploader.upload("small", key, source, chunk_size=50)
                with lock:
                    results["success"] += 1
            except BucketFullError:
                with lock:
                    results["full"] += 1

        threads = []
        for i in range(20):
            t = threading.Thread(target=try_upload, args=(f"f{i}", b"x" * 100))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        total_uploaded = results["success"] * 100
        assert total_uploaded <= 500
