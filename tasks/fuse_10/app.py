from typing import Any, Callable


class JobQueue:
    def __init__(self, max_workers: int = 1) -> None:
        pass

    def submit(self, job_id: str, fn: Callable, priority: int = 0, max_retries: int = 0) -> None:
        raise NotImplementedError

    def get_status(self, job_id: str) -> str:
        raise NotImplementedError

    def get_result(self, job_id: str) -> Any:
        raise NotImplementedError

    def cancel(self, job_id: str) -> bool:
        raise NotImplementedError

    def drain(self) -> None:
        raise NotImplementedError
