from typing import Any


class KVStore:
    def __init__(self, capacity: int) -> None:
        pass

    def put(self, key: str, value: Any, ttl: float | None = None) -> None:
        raise NotImplementedError

    def get(self, key: str) -> Any:
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError

    def keys(self) -> list[str]:
        raise NotImplementedError
