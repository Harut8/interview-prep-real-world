from dataclasses import dataclass


@dataclass
class Response:
    status: int
    body: dict
    retries_used: int = 0


class APIError(Exception):
    def __init__(self, status: int, body: dict):
        self.status = status
        self.body = body


class CircuitOpenError(Exception):
    pass


class APIClient:
    def __init__(self, base_url: str, max_retries: int = 3, rate_limit: int = 10,
                 transport=None, sleep_fn=None) -> None:
        pass

    def get(self, endpoint: str) -> Response:
        raise NotImplementedError

    def post(self, endpoint: str, body: dict) -> Response:
        raise NotImplementedError
