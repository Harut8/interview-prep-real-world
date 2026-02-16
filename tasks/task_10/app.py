import time
import logging
import httpx

logger = logging.getLogger(__name__)


class HttpClient:
    """HTTP client wrapper with retry logic."""

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client = httpx.Client(base_url=base_url)

    def request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # BUG: timeout parameter is not used
                response = self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    params=params,
                )

                self._log_response(response, headers)

                # BUG: retries on ALL non-2xx, should only retry on 5xx
                if response.status_code >= 400:
                    if attempt < self.max_retries:
                        # BUG: not actually exponential — fixed delay
                        time.sleep(self.retry_delay)
                        continue
                    response.raise_for_status()

                return response

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue

            except httpx.HTTPStatusError as e:
                raise

        raise last_exception or RuntimeError("Request failed")

    def _log_response(self, response: httpx.Response, request_headers: dict | None) -> None:
        """Log response details."""
        # BUG: logs sensitive headers
        logger.info(
            f"Response {response.status_code} | "
            f"Request headers: {request_headers} | "
            f"Response headers: {dict(response.headers)}"
        )

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# TODO: Add circuit breaker
# TODO: Add request/response hooks
