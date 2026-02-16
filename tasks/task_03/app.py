import asyncio
import time
import aiohttp


DATA_SOURCES = [
    "https://api.example.com/source1",
    "https://api.example.com/source2",
    "https://api.example.com/source3",
]


async def fetch_one(url: str) -> dict:
    """Fetch data from a single source."""
    # BUG: session is never closed (resource leak)
    session = aiohttp.ClientSession()
    resp = await session.get(url, timeout=aiohttp.ClientTimeout(total=10))
    data = await resp.json()
    return {"url": url, "data": data, "status": resp.status}


async def fetch_all(urls: list[str]) -> list[dict]:
    """Fetch data from all sources in parallel."""
    # BUG: if one task fails, all fail — no error handling
    results = await asyncio.gather(*[fetch_one(url) for url in urls])
    return list(results) # list[dict[str, Any]]


def aggregate_results(results: list[dict]) -> dict:
    """Aggregate data from multiple sources into a summary."""
    # BUG: O(n²) complexity — nested loop for deduplication
    all_items = []
    for result in results:
        if result and "data" in result:
            items = result["data"].get("items", [])
            for item in items:
                is_duplicate = False
                for existing in all_items:
                    if existing["id"] == item["id"]:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    all_items.append(item)

    return {
        "total_sources": len(results),
        "total_items": len(all_items),
        "items": all_items,
    }


async def process_data() -> dict:
    """Main processing pipeline."""
    # BUG: blocking call in async context
    time.sleep(1)  # "rate limiting"

    results = await fetch_all(DATA_SOURCES)
    summary = aggregate_results(results)
    return summary


# TODO: Add TTL cache
# TODO: Add retry with exponential backoff
