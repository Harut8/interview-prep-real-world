import re
import asyncio
import aiohttp
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class ScrapeResult:
    url: str
    status: int
    title: str | None
    links: list[str]
    error: str | None = None


def parse_page(html: str, base_url: str) -> tuple[str | None, list[str]]:
    """Extract title and links from HTML. (Simplified parser)"""
    # BUG: this is a blocking regex operation that could be slow on large pages
    title_match = re.search(r"<title>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else None

    links = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    # Filter to absolute URLs only
    absolute_links = [
        link for link in links
        if link.startswith("http://") or link.startswith("https://")
    ]
    return title, absolute_links


async def fetch_page(url: str) -> ScrapeResult:
    """Fetch a single page."""
    # BUG: creates a new session per request — doesn't share connection pool
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                html = await resp.text()
                title, links = parse_page(html, url)
                return ScrapeResult(
                    url=url, status=resp.status, title=title, links=links
                )
        except Exception as e:
            return ScrapeResult(
                url=url, status=0, title=None, links=[], error=str(e)
            )


async def scrape_all(urls: list[str]) -> list[ScrapeResult]:
    """Scrape all URLs concurrently."""
    # BUG: no concurrency limit — tries to open all connections at once
    # BUG: if gather fails, all results are lost
    tasks = [fetch_page(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return list(results)


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc


# TODO: Add per-domain rate limiting
# TODO: Add progress callback
# TODO: Share aiohttp.ClientSession across requests
# TODO: Add semaphore for concurrency control
