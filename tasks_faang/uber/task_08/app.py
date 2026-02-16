"""
Ride Event Stream Processor
Processes real-time ride lifecycle events.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Ride Event Stream Processor")


class EventType(Enum):
    RIDE_REQUESTED = "RIDE_REQUESTED"
    DRIVER_ACCEPTED = "DRIVER_ACCEPTED"
    RIDE_STARTED = "RIDE_STARTED"
    RIDE_COMPLETED = "RIDE_COMPLETED"
    RIDE_CANCELLED = "RIDE_CANCELLED"


class RideState(Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# Valid state transitions
VALID_TRANSITIONS: dict[RideState, set[RideState]] = {
    RideState.REQUESTED: {RideState.ACCEPTED, RideState.CANCELLED},
    RideState.ACCEPTED: {RideState.STARTED, RideState.CANCELLED},
    RideState.STARTED: {RideState.COMPLETED, RideState.CANCELLED},
    RideState.COMPLETED: set(),
    RideState.CANCELLED: set(),
}

# Map event type to resulting ride state
EVENT_TO_STATE: dict[EventType, RideState] = {
    EventType.RIDE_REQUESTED: RideState.REQUESTED,
    EventType.DRIVER_ACCEPTED: RideState.ACCEPTED,
    EventType.RIDE_STARTED: RideState.STARTED,
    EventType.RIDE_COMPLETED: RideState.COMPLETED,
    EventType.RIDE_CANCELLED: RideState.CANCELLED,
}


@dataclass
class RideEvent:
    event_id: str
    ride_id: str
    event_type: EventType
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RideRecord:
    ride_id: str
    current_state: RideState = RideState.REQUESTED
    events: list[RideEvent] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


# --- In-memory storage ---
rides: dict[str, RideRecord] = {}
processed_events: list[RideEvent] = []
metrics: dict[str, int] = {
    "total_events": 0,
    "total_rides": 0,
    "completed_rides": 0,
    "cancelled_rides": 0,
}


def validate_event(event_data: dict) -> Optional[str]:
    """
    Validate an incoming event.

    BUG: No validation is actually performed — all events pass through.
    Missing fields, invalid types, and negative timestamps are all accepted.
    """
    # BUG: Returns None (valid) for everything — no actual validation
    return None


def process_event(event: RideEvent) -> dict:
    """
    Process a single ride event.

    BUG 1: Does not check for duplicate event_ids — same event processed twice.
    BUG 2: Does not handle out-of-order events — processes in arrival order
           regardless of event timestamp.
    """
    target_state = EVENT_TO_STATE[event.event_type]

    # Handle new ride
    if event.event_type == EventType.RIDE_REQUESTED:
        if event.ride_id not in rides:
            rides[event.ride_id] = RideRecord(
                ride_id=event.ride_id,
                created_at=event.timestamp,
            )
            metrics["total_rides"] += 1

    ride = rides.get(event.ride_id)
    if ride is None:
        return {"status": "error", "message": f"Ride {event.ride_id} not found"}

    # BUG: No duplicate check — same event_id processed multiple times
    # Should check if event_id already in processed_events

    # Check state transition validity
    current_state = ride.current_state
    if target_state not in VALID_TRANSITIONS.get(current_state, set()):
        if event.event_type != EventType.RIDE_REQUESTED:
            # BUG: Out-of-order events are just rejected instead of being
            # buffered and reordered by timestamp
            return {
                "status": "error",
                "message": f"Invalid transition from {current_state.value} to {target_state.value}",
            }

    # Apply state change
    ride.current_state = target_state
    ride.events.append(event)
    ride.updated_at = event.timestamp

    # Update metrics
    metrics["total_events"] += 1
    if target_state == RideState.COMPLETED:
        metrics["completed_rides"] += 1
    elif target_state == RideState.CANCELLED:
        metrics["cancelled_rides"] += 1

    processed_events.append(event)

    return {"status": "ok", "ride_id": event.ride_id, "new_state": target_state.value}


def ingest_events(events: list[dict]) -> list[dict]:
    """
    Ingest a batch of events.

    BUG: Processes events in the order they arrive in the list,
    not sorted by their timestamp field.
    """
    results = []
    for event_data in events:
        # BUG: No validation call
        error = validate_event(event_data)
        if error:
            results.append({"status": "error", "message": error})
            continue

        try:
            event = RideEvent(
                event_id=event_data["event_id"],
                ride_id=event_data["ride_id"],
                event_type=EventType(event_data["event_type"]),
                timestamp=event_data.get("timestamp", time.time()),
                metadata=event_data.get("metadata", {}),
            )
        except (KeyError, ValueError) as e:
            results.append({"status": "error", "message": str(e)})
            continue

        result = process_event(event)
        results.append(result)

    return results


# --- API Endpoints ---

class EventSubmit(BaseModel):
    event_id: str
    ride_id: str
    event_type: str
    timestamp: Optional[float] = None
    metadata: dict[str, Any] = {}


class BatchEvents(BaseModel):
    events: list[dict[str, Any]]


@app.post("/events")
def submit_event(data: EventSubmit):
    event_data = {
        "event_id": data.event_id,
        "ride_id": data.ride_id,
        "event_type": data.event_type,
        "timestamp": data.timestamp or time.time(),
        "metadata": data.metadata,
    }
    results = ingest_events([event_data])
    return results[0]


@app.post("/events/batch")
def submit_batch(data: BatchEvents):
    results = ingest_events(data.events)
    return {"results": results, "count": len(results)}


@app.get("/rides/{ride_id}")
def get_ride(ride_id: str):
    ride = rides.get(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return {
        "ride_id": ride.ride_id,
        "current_state": ride.current_state.value,
        "event_count": len(ride.events),
        "created_at": ride.created_at,
        "updated_at": ride.updated_at,
    }


@app.get("/metrics")
def get_metrics():
    return metrics
