import pytest
from app import APIClient, Response, APIError, CircuitOpenError


class MockTransport:
    def __init__(self, responses: list):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, body=None):
        self.calls.append((method, url, body))
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


class TestBasicRequests:
    def test_get_success(self):
        transport = MockTransport([Response(200, {"ok": True})])
        client = APIClient("http://api.test", transport=transport, sleep_fn=lambda _: None)
        resp = client.get("/health")
        assert resp.status == 200
        assert resp.body == {"ok": True}

    def test_post_success(self):
        transport = MockTransport([Response(201, {"id": 1})])
        client = APIClient("http://api.test", transport=transport, sleep_fn=lambda _: None)
        resp = client.post("/items", {"name": "test"})
        assert resp.status == 201


class TestRetries:
    def test_retries_on_500(self):
        transport = MockTransport([
            Response(500, {"error": "internal"}),
            Response(500, {"error": "internal"}),
            Response(200, {"ok": True}),
        ])
        client = APIClient("http://api.test", max_retries=3, transport=transport, sleep_fn=lambda _: None)
        resp = client.get("/flaky")
        assert resp.status == 200
        assert resp.retries_used == 2

    def test_retries_on_connection_error(self):
        transport = MockTransport([
            ConnectionError("refused"),
            Response(200, {"ok": True}),
        ])
        client = APIClient("http://api.test", max_retries=3, transport=transport, sleep_fn=lambda _: None)
        resp = client.get("/flaky")
        assert resp.status == 200

    def test_no_retry_on_4xx(self):
        transport = MockTransport([Response(404, {"error": "not found"})])
        client = APIClient("http://api.test", max_retries=3, transport=transport, sleep_fn=lambda _: None)
        with pytest.raises(APIError) as exc_info:
            client.get("/missing")
        assert exc_info.value.status == 404
        assert len(transport.calls) == 1

    def test_exhausted_retries(self):
        transport = MockTransport([
            Response(500, {"error": "fail"}),
            Response(500, {"error": "fail"}),
            Response(500, {"error": "fail"}),
            Response(500, {"error": "fail"}),
        ])
        client = APIClient("http://api.test", max_retries=3, transport=transport, sleep_fn=lambda _: None)
        with pytest.raises(APIError):
            client.get("/broken")


class TestBackoff:
    def test_exponential_delays(self):
        delays = []
        transport = MockTransport([
            Response(500, {}),
            Response(500, {}),
            Response(200, {"ok": True}),
        ])
        client = APIClient("http://api.test", max_retries=3, transport=transport, sleep_fn=lambda d: delays.append(d))
        client.get("/slow")
        assert delays == [1, 2]  # 2^0, 2^1


class TestCircuitBreaker:
    def test_circuit_opens_after_failures(self):
        responses = [Response(500, {})] * 10
        transport = MockTransport(responses)
        client = APIClient("http://api.test", max_retries=0, transport=transport, sleep_fn=lambda _: None)
        for _ in range(5):
            try:
                client.get("/fail")
            except APIError:
                pass
        with pytest.raises(CircuitOpenError):
            client.get("/fail")
