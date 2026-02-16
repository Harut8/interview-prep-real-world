"""
Trip Fare Calculator
Calculates ride fares with distance, time, surge, tips, and tolls.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Trip Fare Calculator")

# Pricing constants
BASE_FARE = 2.50
PER_KM_RATE = 1.50
PER_MINUTE_RATE = 0.25
MINIMUM_FARE = 5.00
BOOKING_FEE = 1.75


class TripStatus(Enum):
    ESTIMATED = "estimated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Trip:
    trip_id: str
    rider_id: str
    driver_id: str
    distance_km: float = 0.0
    duration_minutes: float = 0.0
    surge_multiplier: float = 1.0
    tip_amount: float = 0.0
    toll_amount: float = 0.0
    status: TripStatus = TripStatus.IN_PROGRESS
    created_at: float = field(default_factory=time.time)


@dataclass
class FareResult:
    trip_id: str
    base_fare: float
    distance_charge: float
    time_charge: float
    surge_multiplier: float
    surge_amount: float
    tip: float
    tolls: float
    booking_fee: float
    total: float


# --- In-memory storage ---
trips: dict[str, Trip] = {}
fare_results: dict[str, FareResult] = {}


def calculate_fare(trip: Trip) -> FareResult:
    """
    Calculate the fare for a completed trip.

    BUG 1: Floating point arithmetic — no rounding, causes penny errors.
    BUG 2: Tip is included BEFORE surge multiplier is applied.
    BUG 3: No minimum fare enforcement — short trips can produce very low totals.
    """
    base = BASE_FARE
    distance_charge = trip.distance_km * PER_KM_RATE
    time_charge = trip.duration_minutes * PER_MINUTE_RATE

    # BUG: Tip is added before surge! Tip should not be surged.
    subtotal = base + distance_charge + time_charge + trip.tip_amount

    # Apply surge to the subtotal (which incorrectly includes tip)
    surge_amount = subtotal * (trip.surge_multiplier - 1)
    surged_subtotal = subtotal + surge_amount

    # Add tolls and booking fee
    # BUG: No rounding — floating point imprecision accumulates
    total = surged_subtotal + trip.toll_amount + BOOKING_FEE

    # BUG: No minimum fare check — very short trips could cost less than $5

    return FareResult(
        trip_id=trip.trip_id,
        base_fare=base,
        distance_charge=distance_charge,
        time_charge=time_charge,
        surge_multiplier=trip.surge_multiplier,
        surge_amount=surge_amount,
        tip=trip.tip_amount,
        tolls=trip.toll_amount,
        booking_fee=BOOKING_FEE,
        total=total,
    )


# --- API Endpoints ---

class TripCreate(BaseModel):
    trip_id: str
    rider_id: str
    driver_id: str
    distance_km: float
    duration_minutes: float
    surge_multiplier: float = 1.0
    tip_amount: float = 0.0
    toll_amount: float = 0.0


class TripComplete(BaseModel):
    tip_amount: float = 0.0


@app.post("/trips")
def create_trip(data: TripCreate):
    trip = Trip(
        trip_id=data.trip_id,
        rider_id=data.rider_id,
        driver_id=data.driver_id,
        distance_km=data.distance_km,
        duration_minutes=data.duration_minutes,
        surge_multiplier=data.surge_multiplier,
        tip_amount=data.tip_amount,
        toll_amount=data.toll_amount,
    )
    trips[data.trip_id] = trip
    return {"status": "created", "trip_id": data.trip_id}


@app.post("/trips/{trip_id}/complete")
def complete_trip(trip_id: str, data: TripComplete = TripComplete()):
    if trip_id not in trips:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips[trip_id]
    if data.tip_amount > 0:
        trip.tip_amount = data.tip_amount

    trip.status = TripStatus.COMPLETED
    fare = calculate_fare(trip)
    fare_results[trip_id] = fare

    return {
        "trip_id": trip_id,
        "total_fare": fare.total,
        "status": "completed",
    }


@app.get("/trips/{trip_id}/fare")
def get_fare(trip_id: str):
    if trip_id not in fare_results:
        raise HTTPException(status_code=404, detail="Fare not calculated yet")
    fare = fare_results[trip_id]
    return {
        "trip_id": fare.trip_id,
        "base_fare": fare.base_fare,
        "distance_charge": fare.distance_charge,
        "time_charge": fare.time_charge,
        "surge_multiplier": fare.surge_multiplier,
        "surge_amount": fare.surge_amount,
        "tip": fare.tip,
        "tolls": fare.tolls,
        "booking_fee": fare.booking_fee,
        "total": fare.total,
    }


@app.get("/trips")
def list_trips():
    return [
        {
            "trip_id": t.trip_id,
            "rider_id": t.rider_id,
            "driver_id": t.driver_id,
            "status": t.status.value,
            "distance_km": t.distance_km,
            "duration_minutes": t.duration_minutes,
        }
        for t in trips.values()
    ]
