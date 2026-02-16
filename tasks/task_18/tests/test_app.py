import pytest
from app import MiddlewareChain, Middleware, Request, Response, echo_handler


class UpperCaseMiddleware(Middleware):
    """Test middleware that uppercases the path."""
    def process_request(self, request):
        request.path = request.path.upper()
        return request


class AddHeaderMiddleware(Middleware):
    """Test middleware that adds a response header."""
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def process_response(self, request, response):
        response.headers[self.key] = self.value
        return response


@pytest.fixture
def chain():
    c = MiddlewareChain()
    c.set_handler(echo_handler)
    return c


def test_basic_chain(chain):
    request = Request(method="GET", path="/test")
    response = chain.handle(request)
    assert response.status_code == 200


# FAILS — fix middleware ordering
def test_middleware_order(chain):
    order = []

    class TrackingMiddleware(Middleware):
        def __init__(self, name):
            self.name = name
        def process_request(self, request):
            order.append(self.name)
            return request

    chain.add(TrackingMiddleware("first"))
    chain.add(TrackingMiddleware("second"))
    chain.handle(Request(method="GET", path="/test"))
    assert order == ["first", "second"]  # Should execute in add order


# FAILS — fix error handling
def test_error_in_handler_still_runs_response_middleware(chain):
    cleanup_ran = [False]

    class CleanupMiddleware(Middleware):
        def process_response(self, request, response):
            cleanup_ran[0] = True
            return response

    chain.add(CleanupMiddleware())
    chain.set_handler(lambda r: (_ for _ in ()).throw(ValueError("boom")))

    with pytest.raises(ValueError):
        chain.handle(Request(method="GET", path="/test"))

    assert cleanup_ran[0] is True


# FAILS — fix validation
def test_add_invalid_middleware(chain):
    with pytest.raises(TypeError):
        chain.add("not a middleware")


# TODO: Add tests for TimingMiddleware
# TODO: Add tests for AuthMiddleware
# TODO: Add tests for LoggingMiddleware
# TODO: Add test for short-circuit behavior
