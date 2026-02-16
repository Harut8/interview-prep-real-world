import hashlib
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

app = FastAPI()

# In-memory storage
url_storage: dict[str, dict] = {}


class ShortenRequest(BaseModel):
    url: str


class ShortenResponse(BaseModel):
    short_id: str
    short_url: str


def generate_short_id(url: str) -> str:
    hash_val = hashlib.md5(url.encode()).hexdigest()[:6]
    return hash_val


@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(request: ShortenRequest):
    # BUG: No URL validation at all
    short_id = generate_short_id(request.url)
    url_storage[short_id] = {
        "original_url": request.url,
        "created_at": time.time(),
        "click_count": 0,
    }
    return ShortenResponse(
        short_id=short_id,
        short_url=f"http://localhost:8000/{short_id}",
    )


@app.get("/{short_id}")
def redirect_to_url(short_id: str):
    # BUG: doesn't handle missing keys properly
    entry = url_storage[short_id]
    entry["click_count"] += 1
    return RedirectResponse(url=entry["original_url"])


def delete_url(short_id: str) -> bool:
    """Delete a shortened URL from storage."""
    # BUG: doesn't actually delete
    if short_id in url_storage:
        url_storage.get(short_id)
        return True
    return False


# TODO: Add GET /stats/{short_id} endpoint
