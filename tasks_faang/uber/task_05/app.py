"""
Driver Location Tracker
Tracks and queries driver locations in real-time using geohashing.
"""

import time
import math
from dataclasses import dataclass, field
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Driver Location Tracker")

STALE_TIMEOUT_SECONDS = 300  # 5 minutes

# Geohash encoding characters
GEOHASH_CHARS = "0123456789bcdefghjkmnpqrstuvwxyz"

# BUG: Precision 4 is way too low (~40km cells). Should be 6 or 7.
GEOHASH_PRECISION = 4


def encode_geohash(latitude: float, longitude: float, precision: int = GEOHASH_PRECISION) -> str:
    """
    Encode a (latitude, longitude) into a geohash string.

    BUG: Uses the module-level GEOHASH_PRECISION which is too low.
    """
    lat_range = (-90.0, 90.0)
    lon_range = (-180.0, 180.0)
    geohash = []
    bits = 0
    current_char = 0
    is_longitude = True

    while len(geohash) < precision:
        if is_longitude:
            mid = (lon_range[0] + lon_range[1]) / 2
            if longitude >= mid:
                current_char = current_char * 2 + 1
                lon_range = (mid, lon_range[1])
            else:
                current_char = current_char * 2
                lon_range = (lon_range[0], mid)
        else:
            mid = (lat_range[0] + lat_range[1]) / 2
            if latitude >= mid:
                current_char = current_char * 2 + 1
                lat_range = (mid, lat_range[1])
            else:
                current_char = current_char * 2
                lat_range = (lat_range[0], mid)

        is_longitude = not is_longitude
        bits += 1

        if bits == 5:
            geohash.append(GEOHASH_CHARS[current_char])
            bits = 0
            current_char = 0

    return "".join(geohash)


@dataclass
class LocationUpdate:
    driver_id: str
    latitude: float
    longitude: float
    timestamp: float
    geohash: str = ""

    def __post_init__(self):
        if not self.geohash:
            self.geohash = encode_geohash(self.latitude, self.longitude)


@dataclass
class DriverLocation:
    driver_id: str
    latest: Optional[LocationUpdate] = None
    history: list[LocationUpdate] = field(default_factory=list)


# --- In-memory storage ---
driver_locations: dict[str, DriverLocation] = {}
# Spatial index: geohash -> set of driver_ids
geohash_index: dict[str, set[str]] = {}


def update_driver_location(driver_id: str, latitude: float,
                           longitude: float, timestamp: float) -> LocationUpdate:
    """
    Record a new location update for a driver.

    BUG: History is appended but never sorted by timestamp.
    Late-arriving updates break the ordering.
    """
    update = LocationUpdate(
        driver_id=driver_id,
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
    )

    if driver_id not in driver_locations:
        driver_locations[driver_id] = DriverLocation(driver_id=driver_id)

    loc = driver_locations[driver_id]

    # Remove from old geohash index
    if loc.latest and loc.latest.geohash in geohash_index:
        geohash_index[loc.latest.geohash].discard(driver_id)

    # BUG: Just appends, doesn't maintain sorted order by timestamp
    loc.history.append(update)

    # Set as latest (but doesn't check if it's actually the newest by timestamp)
    loc.latest = update

    # Add to new geohash index
    if update.geohash not in geohash_index:
        geohash_index[update.geohash] = set()
    geohash_index[update.geohash].add(driver_id)

    return update


def get_nearby_drivers(latitude: float, longitude: float) -> list[DriverLocation]:
    """
    Get all drivers near a location using geohash prefix matching.

    BUG: No stale location cleanup — returns drivers who went offline hours ago.
    """
    geohash = encode_geohash(latitude, longitude)

    # Find all drivers in the same geohash cell
    nearby = []
    driver_ids = geohash_index.get(geohash, set())

    for did in driver_ids:
        loc = driver_locations.get(did)
        if loc and loc.latest:
            # BUG: No staleness check — should exclude locations older than STALE_TIMEOUT_SECONDS
            nearby.append(loc)

    return nearby


def get_driver_latest_location(driver_id: str) -> Optional[LocationUpdate]:
    """Get the latest location for a driver."""
    loc = driver_locations.get(driver_id)
    if loc is None or loc.latest is None:
        return None
    return loc.latest


def get_driver_history(driver_id: str, since: Optional[float] = None) -> list[LocationUpdate]:
    """
    Get location history for a driver.

    BUG: Returns unsorted history. Late-arriving updates are out of order.
    """
    loc = driver_locations.get(driver_id)
    if loc is None:
        return []

    history = loc.history
    if since is not None:
        history = [h for h in history if h.timestamp >= since]

    # BUG: Does not sort by timestamp — returns in insertion order
    return history


# --- API Endpoints ---

class LocationUpdateRequest(BaseModel):
    driver_id: str
    latitude: float
    longitude: float
    timestamp: Optional[float] = None


class NearbyQuery(BaseModel):
    latitude: float
    longitude: float


@app.post("/location/update")
def api_update_location(data: LocationUpdateRequest):
    ts = data.timestamp if data.timestamp else time.time()
    update = update_driver_location(data.driver_id, data.latitude,
                                    data.longitude, ts)
    return {
        "driver_id": update.driver_id,
        "geohash": update.geohash,
        "timestamp": update.timestamp,
    }


@app.post("/location/nearby")
def api_nearby_drivers(query: NearbyQuery):
    nearby = get_nearby_drivers(query.latitude, query.longitude)
    return [
        {
            "driver_id": loc.driver_id,
            "latitude": loc.latest.latitude,
            "longitude": loc.latest.longitude,
            "timestamp": loc.latest.timestamp,
            "geohash": loc.latest.geohash,
        }
        for loc in nearby
        if loc.latest
    ]


@app.get("/location/{driver_id}")
def api_get_location(driver_id: str):
    loc = get_driver_latest_location(driver_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {
        "driver_id": loc.driver_id,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "timestamp": loc.timestamp,
        "geohash": loc.geohash,
    }


@app.get("/location/{driver_id}/history")
def api_get_history(driver_id: str, since: Optional[float] = None):
    history = get_driver_history(driver_id, since)
    return [
        {
            "latitude": h.latitude,
            "longitude": h.longitude,
            "timestamp": h.timestamp,
        }
        for h in history
    ]
