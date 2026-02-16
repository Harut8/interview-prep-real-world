"""
Surge Pricing Calculator
Dynamic pricing based on supply/demand ratio in geographic zones.
"""

import math
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Surge Pricing Calculator")


@dataclass
class Location:
    latitude: float
    longitude: float


@dataclass
class Zone:
    zone_id: str
    name: str
    center: Location
    radius_km: float  # Circular zone boundary
    base_fare: float = 5.0


@dataclass
class ZoneState:
    zone_id: str
    demand_count: int = 0  # Number of ride requests
    supply_count: int = 0  # Number of available drivers
    current_multiplier: float = 1.0
    last_updated: float = field(default_factory=time.time)


# --- In-memory storage ---
zones: dict[str, Zone] = {}
zone_states: dict[str, ZoneState] = {}
surge_history: list[dict] = []


def haversine_distance(loc1: Location, loc2: Location) -> float:
    """Calculate distance between two points in kilometers."""
    R = 6371
    lat1, lat2 = math.radians(loc1.latitude), math.radians(loc2.latitude)
    dlat = math.radians(loc2.latitude - loc1.latitude)
    dlon = math.radians(loc2.longitude - loc1.longitude)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def find_zone_for_location(location: Location) -> Optional[Zone]:
    """
    Find which zone a location belongs to.

    BUG: When zones overlap, this returns the LAST matching zone
    instead of the most specific (smallest radius) one.
    """
    matching_zone = None
    for zone in zones.values():
        dist = haversine_distance(location, zone.center)
        if dist <= zone.radius_km:
            # BUG: Always overwrites, so last match wins instead of
            # the most specific (smallest) zone
            matching_zone = zone
    return matching_zone


def calculate_surge_multiplier(zone_id: str) -> float:
    """
    Calculate surge multiplier for a zone based on supply/demand.

    BUG 1: Division by zero when supply_count is 0 — should return max surge.
    BUG 2: No cap on the multiplier — can grow unboundedly.
    """
    state = zone_states.get(zone_id)
    if state is None:
        return 1.0

    # BUG: Crashes when supply_count is 0
    raw_ratio = state.demand_count / state.supply_count

    # BUG: No maximum cap on the multiplier
    multiplier = max(1.0, raw_ratio)

    # Update state
    state.current_multiplier = multiplier
    state.last_updated = time.time()

    # Record history
    surge_history.append({
        "zone_id": zone_id,
        "multiplier": multiplier,
        "demand": state.demand_count,
        "supply": state.supply_count,
        "timestamp": time.time(),
    })

    return multiplier


def get_surge_price(zone_id: str, base_fare: Optional[float] = None) -> dict:
    """Get the current surged price for a zone."""
    zone = zones.get(zone_id)
    if zone is None:
        raise ValueError(f"Zone {zone_id} not found")

    fare = base_fare if base_fare is not None else zone.base_fare
    multiplier = calculate_surge_multiplier(zone_id)

    return {
        "zone_id": zone_id,
        "base_fare": fare,
        "multiplier": round(multiplier, 2),
        "surged_fare": round(fare * multiplier, 2),
    }


# --- API Endpoints ---

class ZoneCreate(BaseModel):
    zone_id: str
    name: str
    center_lat: float
    center_lon: float
    radius_km: float
    base_fare: float = 5.0


class DemandSupplyUpdate(BaseModel):
    demand_count: int
    supply_count: int


class LocationQuery(BaseModel):
    latitude: float
    longitude: float


@app.post("/zones")
def create_zone(data: ZoneCreate):
    zone = Zone(
        zone_id=data.zone_id,
        name=data.name,
        center=Location(latitude=data.center_lat, longitude=data.center_lon),
        radius_km=data.radius_km,
        base_fare=data.base_fare,
    )
    zones[data.zone_id] = zone
    zone_states[data.zone_id] = ZoneState(zone_id=data.zone_id)
    return {"status": "created", "zone_id": data.zone_id}


@app.put("/zones/{zone_id}/demand-supply")
def update_demand_supply(zone_id: str, data: DemandSupplyUpdate):
    if zone_id not in zone_states:
        raise HTTPException(status_code=404, detail="Zone not found")
    state = zone_states[zone_id]
    state.demand_count = data.demand_count
    state.supply_count = data.supply_count
    return {"status": "updated"}


@app.get("/zones/{zone_id}/surge")
def get_zone_surge(zone_id: str):
    if zone_id not in zones:
        raise HTTPException(status_code=404, detail="Zone not found")
    try:
        return get_surge_price(zone_id)
    except ZeroDivisionError:
        raise HTTPException(status_code=500, detail="Internal calculation error")


@app.post("/zones/locate")
def locate_zone(query: LocationQuery):
    location = Location(latitude=query.latitude, longitude=query.longitude)
    zone = find_zone_for_location(location)
    if zone is None:
        raise HTTPException(status_code=404, detail="No zone found for location")
    return {"zone_id": zone.zone_id, "zone_name": zone.name}


@app.get("/zones")
def list_zones():
    return [
        {
            "zone_id": z.zone_id,
            "name": z.name,
            "center_lat": z.center.latitude,
            "center_lon": z.center.longitude,
            "radius_km": z.radius_km,
            "base_fare": z.base_fare,
            "current_multiplier": zone_states[z.zone_id].current_multiplier
            if z.zone_id in zone_states else 1.0,
        }
        for z in zones.values()
    ]
