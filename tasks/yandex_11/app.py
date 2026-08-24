import threading
from typing import BinaryIO, Callable


class BucketFullError(Exception):
    pass


class ObjectNotFoundError(Exception):
    pass


class BucketNotFoundError(Exception):
    pass


class Bucket:
    def __init__(self, name: str, capacity_bytes: int) -> None:
        pass

    def available_space(self) -> int:
        raise NotImplementedError

    def has_object(self, key: str) -> bool:
        raise NotImplementedError


class StorageClient:
    def __init__(self) -> None:
        pass

    def create_bucket(self, name: str, capacity_bytes: int) -> Bucket:
        raise NotImplementedError

    def upload(self, bucket: str, key: str, data: bytes) -> str:
        raise NotImplementedError

    def download(self, bucket: str, key: str) -> bytes:
        raise NotImplementedError

    def delete(self, bucket: str, key: str) -> None:
        raise NotImplementedError

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        raise NotImplementedError

    def multipart_upload(self, bucket: str, key: str, source: BinaryIO,
                         chunk_size: int = 8 * 1024 * 1024) -> str:
        raise NotImplementedError


class ConcurrentUploader:
    def __init__(self, client: StorageClient, max_workers: int = 4) -> None:
        pass

    def upload(self, bucket: str, key: str, source: BinaryIO,
               chunk_size: int = 8 * 1024 * 1024,
               on_progress: Callable[[int], None] | None = None) -> str:
        raise NotImplementedError
