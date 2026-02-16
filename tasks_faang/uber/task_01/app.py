"""
Ride Matching Service
Matches riders with nearest available drivers based on location.
"""

import math
import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Ride Matching Service")


class DriverStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class Location:
    latitude: float
    longitude: float


@dataclass
class Driver:
    driver_id: str
    name: str
    location: Location
    status: DriverStatus = DriverStatus.AVAILABLE
    rating: float = 5.0
    total_rides: int = 0


@dataclass
class Rider:
    rider_id: str
    name: str
    location: Location


@dataclass
class MatchResult:
    driver_id: str
    rider_id: str
    distance_km: float
    estimated_eta_minutes: float
    timestamp: float = field(default_factory=time.time)


class MatchRequest(BaseModel):
    rider_id: str
    latitude: float
    longitude: float


class MatchResponse(BaseModel):
    driver_id: str
    driver_name: str
    distance_km: float
    eta_minutes: float


# --- In-memory storage ---
drivers: dict[str, Driver] = {}
riders: dict[str, Rider] = {}
match_history: list[MatchResult] = []


def haversine_distance(loc1: Location, loc2: Location) -> float:
    """
    Calculate the great-circle distance between two points
    on Earth using the Haversine formula.
    Returns distance in kilometers.

    BUG: The formula has an error - it uses addition instead of
    subtraction for delta calculations, producing wrong distances.
    """
    R = 6371  # Earth's radius in km

    lat1 = math.radians(loc1.latitude)
    lat2 = math.radians(loc2.latitude)
    # BUG: should be loc2.latitude - loc1.latitude, but using addition
    dlat = math.radians(loc2.latitude + loc1.latitude)
    dlon = math.radians(loc2.longitude + loc1.longitude)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def estimate_eta(distance_km: float, avg_speed_kmh: float = 30.0) -> float:
    """Estimate time of arrival in minutes given distance and average speed."""
    return (distance_km / avg_speed_kmh) * 60


def find_nearest_driver(rider_location: Location) -> Optional[Driver]:
    """
    Find the nearest available driver to the rider.

    BUG: Driver status is not updated atomically. Between checking
    availability and assigning, another thread could match the same driver.
    """
    available_drivers = [
        d for d in drivers.values() if d.status == DriverStatus.AVAILABLE
    ]

    if not available_drivers:
        return None

    nearest = min(
        available_drivers,
        key=lambda d: haversine_distance(rider_location, d.location)
    )

    # BUG: No lock/atomic update — race condition between finding and updating
    nearest.status = DriverStatus.BUSY

    return nearest


def match_rider_with_driver(rider_id: str, rider_lat: float, rider_lon: float) -> Optional[MatchResult]:
    """
    Match a rider with the best available driver.

    BUG: No timeout — if no drivers available, this could conceptually
    hang or just return None without any retry/timeout mechanism.
    The caller has no way to specify a timeout or get notified.
    """
    rider_location = Location(latitude=rider_lat, longitude=rider_lon)

    driver = find_nearest_driver(rider_location)
    if driver is None:
        # BUG: No timeout/retry mechanism - just returns None immediately
        return None

    distance = haversine_distance(rider_location, driver.location)
    eta = estimate_eta(distance)

    result = MatchResult(
        driver_id=driver.driver_id,
        rider_id=rider_id,
        distance_km=distance,
        estimated_eta_minutes=eta,
    )
    match_history.append(result)
    return result


# --- API Endpoints ---

class DriverCreate(BaseModel):
    driver_id: str
    name: str
    latitude: float
    longitude: float
    rating: float = 5.0


class DriverStatusUpdate(BaseModel):
    status: str


@app.post("/drivers")
def create_driver(data: DriverCreate):
    driver = Driver(
        driver_id=data.driver_id,
        name=data.name,
        location=Location(latitude=data.latitude, longitude=data.longitude),
        rating=data.rating,
    )
    drivers[data.driver_id] = driver
    return {"status": "created", "driver_id": data.driver_id}


@app.patch("/drivers/{driver_id}/status")
def update_driver_status(driver_id: str, data: DriverStatusUpdate):
    if driver_id not in drivers:
        raise HTTPException(status_code=404, detail="Driver not found")
    drivers[driver_id].status = DriverStatus(data.status)
    return {"status": "updated"}


@app.post("/match", response_model=MatchResponse)
def request_match(request: MatchRequest):
    result = match_rider_with_driver(
        rider_id=request.rider_id,
        rider_lat=request.latitude,
        rider_lon=request.longitude,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No drivers available")

    driver = drivers[result.driver_id]
    return MatchResponse(
        driver_id=driver.driver_id,
        driver_name=driver.name,
        distance_km=round(result.distance_km, 2),
        eta_minutes=round(result.estimated_eta_minutes, 1),
    )


@app.get("/drivers")
def list_drivers():
    return [
        {
            "driver_id": d.driver_id,
            "name": d.name,
            "status": d.status.value,
            "latitude": d.location.latitude,
            "longitude": d.location.longitude,
            "rating": d.rating,
        }
        for d in drivers.values()
    ]


@app.get("/match/history")
def get_match_history():
    return match_history
