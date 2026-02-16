"""
Fleet Analytics Dashboard API
Provides fleet utilization metrics, peak hours, and trip analytics.
"""

import time
import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Fleet Analytics Dashboard API")


class DriverStatus(Enum):
    ONLINE_AVAILABLE = "online_available"
    ONLINE_BUSY = "online_busy"
    OFFLINE = "offline"


@dataclass
class TripRecord:
    trip_id: str
    driver_id: str
    zone: str
    started_at: float  # UTC epoch
    completed_at: float  # UTC epoch
    fare_cents: int
    wait_time_seconds: float  # Time rider waited for pickup
    duration_minutes: float


@dataclass
class DriverSnapshot:
    driver_id: str
    status: DriverStatus
    zone: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class DailyMetric:
    date: str  # YYYY-MM-DD
    total_trips: int = 0
    total_fare_cents: int = 0
    avg_duration_minutes: float = 0.0
    avg_wait_seconds: float = 0.0


# City timezone offsets in hours from UTC
CITY_TIMEZONE_OFFSETS: dict[str, int] = {
    "san_francisco": -8,
    "new_york": -5,
    "london": 0,
    "mumbai": 5,  # Actually +5:30 but simplified
    "sao_paulo": -3,
}


# --- In-memory storage ---
trip_records: list[TripRecord] = []
driver_snapshots: dict[str, DriverSnapshot] = {}
daily_metrics: dict[str, DailyMetric] = {}  # date -> metrics


def calculate_moving_average(values: list[float], window: int = 7) -> list[float]:
    """
    Calculate moving average over a list of values.

    BUG: The window slice is off by one — for window=7 it only averages
    6 values because the slice start index is wrong.
    """
    if len(values) < window:
        return [sum(values) / len(values)] if values else []

    result = []
    for i in range(window - 1, len(values)):
        # BUG: Should be `i - window + 1` but uses `i - window + 2`
        # This makes the window 6 instead of 7
        window_values = values[i - window + 2: i + 1]
        avg = sum(window_values) / len(window_values)
        result.append(round(avg, 2))

    return result


def detect_peak_hours(trips: list[TripRecord], city: str = "san_francisco") -> list[dict]:
    """
    Detect peak hours based on trip start times.

    BUG: Uses UTC hour directly without converting to local timezone.
    Reports UTC hours as if they were local times.
    """
    hour_counts: dict[int, int] = {}

    for trip in trips:
        # BUG: This extracts the UTC hour, not the local hour
        utc_dt = datetime.fromtimestamp(trip.started_at, tz=timezone.utc)
        hour = utc_dt.hour  # This is UTC hour!
        hour_counts[hour] = hour_counts.get(hour, 0) + 1

    # Sort by trip count descending
    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)

    return [
        {"hour": h, "trip_count": c, "city": city}
        for h, c in sorted_hours[:5]  # Top 5 peak hours
    ]


def calculate_utilization(zone: Optional[str] = None) -> dict:
    """
    Calculate fleet utilization percentage.

    BUG: busy_count includes drivers with status ONLINE_BUSY even if they
    subsequently went OFFLINE (stale status). total_count only counts
    currently ONLINE drivers. So busy > total is possible -> >100%.
    """
    all_drivers = driver_snapshots.values()
    if zone:
        all_drivers = [d for d in all_drivers if d.zone == zone]
    else:
        all_drivers = list(all_drivers)

    # BUG: total_count only counts ONLINE drivers (available + busy who are online)
    online_drivers = [
        d for d in all_drivers
        if d.status in (DriverStatus.ONLINE_AVAILABLE, DriverStatus.ONLINE_BUSY)
    ]
    total_count = len(online_drivers)

    # BUG: busy_count counts ALL drivers marked busy, including ones
    # who may have gone offline but their snapshot still says ONLINE_BUSY
    # In reality, some "busy" entries are stale
    busy_count = len([d for d in all_drivers if d.status == DriverStatus.ONLINE_BUSY])

    if total_count == 0:
        return {"utilization_pct": 0.0, "online": 0, "busy": 0}

    # BUG: busy_count can exceed total_count if stale entries exist
    utilization = (busy_count / total_count) * 100

    return {
        "utilization_pct": round(utilization, 1),
        "online": total_count,
        "busy": busy_count,
    }


def get_daily_trip_counts(days: int = 30) -> list[DailyMetric]:
    """Get daily metrics for the last N days."""
    now = time.time()
    cutoff = now - (days * 86400)

    results: dict[str, DailyMetric] = {}

    for trip in trip_records:
        if trip.completed_at < cutoff:
            continue
        date_str = datetime.fromtimestamp(
            trip.completed_at, tz=timezone.utc
        ).strftime("%Y-%m-%d")

        if date_str not in results:
            results[date_str] = DailyMetric(date=date_str)

        metric = results[date_str]
        metric.total_trips += 1
        metric.total_fare_cents += trip.fare_cents

    # Calculate averages
    for date_str, metric in results.items():
        day_trips = [
            t for t in trip_records
            if datetime.fromtimestamp(t.completed_at, tz=timezone.utc).strftime("%Y-%m-%d") == date_str
        ]
        if day_trips:
            metric.avg_duration_minutes = round(
                sum(t.duration_minutes for t in day_trips) / len(day_trips), 1
            )
            metric.avg_wait_seconds = round(
                sum(t.wait_time_seconds for t in day_trips) / len(day_trips), 1
            )

    return sorted(results.values(), key=lambda m: m.date)


# --- API Endpoints ---

class TripRecordCreate(BaseModel):
    trip_id: str
    driver_id: str
    zone: str
    started_at: float
    completed_at: float
    fare_cents: int
    wait_time_seconds: float = 0.0
    duration_minutes: float = 0.0


class DriverSnapshotCreate(BaseModel):
    driver_id: str
    status: str
    zone: str


@app.post("/trips")
def record_trip(data: TripRecordCreate):
    trip = TripRecord(
        trip_id=data.trip_id,
        driver_id=data.driver_id,
        zone=data.zone,
        started_at=data.started_at,
        completed_at=data.completed_at,
        fare_cents=data.fare_cents,
        wait_time_seconds=data.wait_time_seconds,
        duration_minutes=data.duration_minutes,
    )
    trip_records.append(trip)
    return {"status": "recorded", "trip_id": data.trip_id}


@app.post("/drivers/snapshot")
def record_driver_snapshot(data: DriverSnapshotCreate):
    snapshot = DriverSnapshot(
        driver_id=data.driver_id,
        status=DriverStatus(data.status),
        zone=data.zone,
    )
    driver_snapshots[data.driver_id] = snapshot
    return {"status": "recorded"}


@app.get("/analytics/utilization")
def api_utilization(zone: Optional[str] = None):
    return calculate_utilization(zone)


@app.get("/analytics/peak-hours")
def api_peak_hours(city: str = "san_francisco"):
    return detect_peak_hours(trip_records, city)


@app.get("/analytics/daily")
def api_daily_metrics(days: int = 30):
    metrics = get_daily_trip_counts(days)
    return [
        {
            "date": m.date,
            "total_trips": m.total_trips,
            "total_fare_cents": m.total_fare_cents,
            "avg_duration_minutes": m.avg_duration_minutes,
            "avg_wait_seconds": m.avg_wait_seconds,
        }
        for m in metrics
    ]


@app.get("/analytics/moving-average")
def api_moving_average(window: int = 7, days: int = 30):
    metrics = get_daily_trip_counts(days)
    trip_counts = [m.total_trips for m in metrics]
    ma = calculate_moving_average(trip_counts, window)
    return {"window": window, "moving_averages": ma}
