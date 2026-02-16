"""Tests for the URL Router / API Gateway."""

import pytest
from app import Router, Request, Response, HTTPMethod, Route


def make_handler(name: str):
    """Create a handler that returns a response with the handler name."""
    def handler(req: Request, params: dict[str, str]) -> Response:
        return Response(status_code=200, body={"handler": name, "params": params})
    return handler


@pytest.fixture
def router() -> Router:
    r = Router()
    r.add_route(HTTPMethod.GET, "/users/{id}", make_handler("get_user"))
    r.add_route(HTTPMethod.GET, "/users/profile", make_handler("get_profile"))
    r.add_route(HTTPMethod.POST, "/users", make_handler("create_user"))
    r.add_route(HTTPMethod.GET, "/posts/{post_id}/comments/{comment_id}", make_handler("get_comment"))
    return r


class TestBasicRouting:
    """Tests for basic routing — some pass, some fail due to bugs."""

    def test_simple_route_match(self, router: Router) -> None:
        """Static route should match exactly."""
        req = Request(method=HTTPMethod.POST, path="/users")
        resp = router.dispatch(req)
        assert resp.status_code == 200
        assert resp.body["handler"] == "create_user"

    def test_param_route_match(self, router: Router) -> None:
        """Parameterized route should extract parameters."""
        req = Request(method=HTTPMethod.GET, path="/users/42")
        resp = router.dispatch(req)
        assert resp.status_code == 200
        assert resp.body["params"]["id"] == "42"

    def test_not_found(self, router: Router) -> None:
        """Non-existent route should return 404."""
        req = Request(method=HTTPMethod.GET, path="/nonexistent")
        resp = router.dispatch(req)
        assert resp.status_code == 404

    def test_multi_param_route(self, router: Router) -> None:
        """Route with multiple parameters should extract all of them."""
        req = Request(method=HTTPMethod.GET, path="/posts/10/comments/5")
        resp = router.dispatch(req)
        assert resp.status_code == 200
        assert resp.body["params"]["post_id"] == "10"
        assert resp.body["params"]["comment_id"] == "5"


class TestRoutePriority:
    """Tests for route matching priority — FAILING due to Bug #1."""

    def test_static_over_parameterized(self, router: Router) -> None:
        """Static route /users/profile should match over /users/{id}.
        FAILING: Bug #1 — greedy matching returns first match (/users/{id}).
        """
        req = Request(method=HTTPMethod.GET, path="/users/profile")
        resp = router.dispatch(req)
        assert resp.body["handler"] == "get_profile", (
            f"Expected 'get_profile' handler for /users/profile, "
            f"got '{resp.body['handler']}'. Static routes should take priority."
        )


class TestSpecialCharacters:
    """Tests for path params with special characters — FAILING due to Bug #2."""

    def test_param_with_hyphen(self, router: Router) -> None:
        """Path parameter should support hyphens.
        FAILING: Bug #2 — regex [a-zA-Z0-9_]+ doesn't match hyphens.
        """
        req = Request(method=HTTPMethod.GET, path="/users/john-doe")
        resp = router.dispatch(req)
        assert resp.status_code == 200
        assert resp.body["params"]["id"] == "john-doe"

    def test_param_with_dot(self, router: Router) -> None:
        """Path parameter should support dots (e.g., filenames).
        FAILING: Bug #2 — regex doesn't match dots.
        """
        router_with_files = Router()
        router_with_files.add_route(HTTPMethod.GET, "/files/{filename}", make_handler("get_file"))
        req = Request(method=HTTPMethod.GET, path="/files/report.pdf")
        resp = router_with_files.dispatch(req)
        assert resp.status_code == 200
        assert resp.body["params"]["filename"] == "report.pdf"


class TestDuplicateRoutes:
    """Tests for duplicate route detection — FAILING due to Bug #3."""

    def test_duplicate_route_raises_error(self) -> None:
        """Registering the same route twice should raise an error.
        FAILING: Bug #3 — silently adds a duplicate.
        """
        r = Router()
        r.add_route(HTTPMethod.GET, "/users/{id}", make_handler("handler_v1"))
        with pytest.raises(ValueError):
            r.add_route(HTTPMethod.GET, "/users/{id}", make_handler("handler_v2"))


class TestMiddleware:
    """Tests for middleware — TODO: implement."""

    def test_middleware_runs_before_handler(self) -> None:
        """TODO: Middleware should execute before the handler."""
        r = Router()
        call_order: list[str] = []

        def logging_middleware(req, params, next_handler):
            call_order.append("middleware")
            return next_handler(req, params)

        def handler(req, params):
            call_order.append("handler")
            return Response(status_code=200, body="ok")

        r.add_route_with_middleware(
            HTTPMethod.GET, "/test", handler, middleware=[logging_middleware]
        )
        resp = r.dispatch_with_middleware(Request(method=HTTPMethod.GET, path="/test"))
        assert call_order == ["middleware", "handler"]


class TestRouteGroups:
    """Tests for route groups — TODO: implement."""

    def test_group_prefix(self) -> None:
        """TODO: Routes in a group should have the prefix prepended."""
        r = Router()
        api = r.group("/api/v1")
        api.add_route(HTTPMethod.GET, "/users", make_handler("list_users"))

        result = r.match(HTTPMethod.GET, "/api/v1/users")
        assert result is not None


class TestWildcardRoutes:
    """Tests for wildcard routes — TODO: implement."""

    def test_wildcard_catches_all(self) -> None:
        """TODO: Wildcard route should match any remaining path segments."""
        r = Router()
        r.add_wildcard_route(HTTPMethod.GET, "/static/{path:*}", make_handler("serve_static"))

        result = r.match(HTTPMethod.GET, "/static/css/main.css")
        assert result is not None
        route, params = result
        assert params["path"] == "css/main.css"
