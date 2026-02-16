import pytest
from app import parse_page, get_domain, ScrapeResult


def test_parse_page_with_title():
    html = "<html><head><title>Test Page</title></head><body></body></html>"
    title, links = parse_page(html, "https://example.com")
    assert title == "Test Page"
    assert links == []


def test_parse_page_with_links():
    html = '<html><body><a href="https://example.com/page1">Link</a></body></html>'
    title, links = parse_page(html, "https://example.com")
    assert "https://example.com/page1" in links


def test_get_domain():
    assert get_domain("https://example.com/path") == "example.com"
    assert get_domain("https://sub.example.com:8080/path") == "sub.example.com:8080"


# TODO: Write async tests for fetch_page with mocked responses
# TODO: Test that session is shared (not one per request)
# TODO: Test concurrency limit (semaphore)
# TODO: Test per-domain rate limiting
# TODO: Test progress callback
# TODO: Test error handling — one failing URL doesn't kill others
