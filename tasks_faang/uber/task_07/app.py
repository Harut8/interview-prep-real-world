"""
Rating & Review System
Bidirectional rating system for riders and drivers.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Rating & Review System")

RATING_WINDOW_SECONDS = 86400  # 24 hours
CACHE_TTL_SECONDS = 300  # 5 minutes


class RaterType(Enum):
    RIDER = "rider"
    DRIVER = "driver"


class ReviewStatus(Enum):
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


@dataclass
class Trip:
    trip_id: str
    rider_id: str
    driver_id: str
    completed_at: float  # Unix timestamp when trip completed


@dataclass
class Rating:
    rating_id: str
    trip_id: str
    rater_id: str  # Who is giving the rating
    ratee_id: str  # Who is being rated
    rater_type: RaterType
    stars: int  # 1-5
    review_text: str = ""
    review_status: ReviewStatus = ReviewStatus.APPROVED
    created_at: float = field(default_factory=time.time)


@dataclass
class UserProfile:
    user_id: str
    user_type: RaterType
    total_rides: int = 0
    total_ratings_received: int = 0
    rating_sum: int = 0
    average_rating: float = 5.0


@dataclass
class CachedAverage:
    user_id: str
    average: float
    calculated_at: float = field(default_factory=time.time)


# --- In-memory storage ---
trips: dict[str, Trip] = {}
ratings: dict[str, Rating] = {}
profiles: dict[str, UserProfile] = {}
average_cache: dict[str, CachedAverage] = {}


def is_within_rating_window(trip: Trip) -> bool:
    """
    Check if the rating window is still open for a trip.

    BUG: The comparison is inverted. It returns True when the window
    has EXPIRED and False when it's still open.
    """
    elapsed = time.time() - trip.completed_at
    # BUG: Should be `elapsed < RATING_WINDOW_SECONDS` (True if within window)
    # but returns True when elapsed > window (expired)
    return elapsed > RATING_WINDOW_SECONDS


def calculate_average_rating(user_id: str) -> float:
    """
    Calculate the average rating for a user.

    BUG: Uses total_rides as the denominator instead of total_ratings_received.
    Drivers who have more rides than ratings get a deflated average.
    """
    profile = profiles.get(user_id)
    if profile is None:
        return 5.0

    # BUG: Should divide by total_ratings_received, not total_rides
    if profile.total_rides == 0:
        return 5.0

    return profile.rating_sum / profile.total_rides


def get_cached_average(user_id: str) -> Optional[float]:
    """Get cached average rating if not expired."""
    entry = average_cache.get(user_id)
    if entry is None:
        return None
    if time.time() - entry.calculated_at > CACHE_TTL_SECONDS:
        del average_cache[user_id]
        return None
    return entry.average


def submit_rating(trip_id: str, rater_id: str, rater_type: RaterType,
                  stars: int, review_text: str = "") -> Rating:
    """
    Submit a rating for a trip.

    BUG: After submitting, does not invalidate the average_cache for the ratee.
    """
    if stars < 1 or stars > 5:
        raise ValueError("Stars must be between 1 and 5")

    trip = trips.get(trip_id)
    if trip is None:
        raise ValueError(f"Trip {trip_id} not found")

    # Determine who is being rated
    if rater_type == RaterType.RIDER:
        ratee_id = trip.driver_id
    else:
        ratee_id = trip.rider_id

    # Check rating window
    if not is_within_rating_window(trip):
        raise ValueError("Rating window has expired")

    # Check for duplicate rating
    for r in ratings.values():
        if r.trip_id == trip_id and r.rater_id == rater_id:
            raise ValueError("Already rated this trip")

    rating_id = f"r_{trip_id}_{rater_id}"
    rating = Rating(
        rating_id=rating_id,
        trip_id=trip_id,
        rater_id=rater_id,
        ratee_id=ratee_id,
        rater_type=rater_type,
        stars=stars,
        review_text=review_text,
    )
    ratings[rating_id] = rating

    # Update profile
    if ratee_id not in profiles:
        profiles[ratee_id] = UserProfile(
            user_id=ratee_id,
            user_type=RaterType.DRIVER if rater_type == RaterType.RIDER else RaterType.RIDER,
        )

    profile = profiles[ratee_id]
    profile.total_ratings_received += 1
    profile.rating_sum += stars
    profile.average_rating = calculate_average_rating(ratee_id)

    # BUG: Does NOT invalidate cache — stale average remains in average_cache

    return rating


# --- API Endpoints ---

class TripCreate(BaseModel):
    trip_id: str
    rider_id: str
    driver_id: str
    completed_at: Optional[float] = None


class RatingSubmit(BaseModel):
    trip_id: str
    rater_id: str
    rater_type: str  # "rider" or "driver"
    stars: int
    review_text: str = ""


@app.post("/trips")
def create_trip(data: TripCreate):
    completed = data.completed_at if data.completed_at else time.time()
    trip = Trip(
        trip_id=data.trip_id,
        rider_id=data.rider_id,
        driver_id=data.driver_id,
        completed_at=completed,
    )
    trips[data.trip_id] = trip
    # Initialize profiles with ride count
    for uid in [data.rider_id, data.driver_id]:
        if uid not in profiles:
            profiles[uid] = UserProfile(user_id=uid, user_type=RaterType.RIDER)
        profiles[uid].total_rides += 1
    return {"status": "created", "trip_id": data.trip_id}


@app.post("/ratings")
def api_submit_rating(data: RatingSubmit):
    try:
        rating = submit_rating(
            data.trip_id, data.rater_id, RaterType(data.rater_type),
            data.stars, data.review_text,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "rating_id": rating.rating_id,
        "stars": rating.stars,
        "ratee_id": rating.ratee_id,
    }


@app.get("/users/{user_id}/rating")
def get_user_rating(user_id: str):
    cached = get_cached_average(user_id)
    if cached is not None:
        return {"user_id": user_id, "average_rating": round(cached, 2), "cached": True}

    avg = calculate_average_rating(user_id)
    average_cache[user_id] = CachedAverage(user_id=user_id, average=avg)
    return {"user_id": user_id, "average_rating": round(avg, 2), "cached": False}


@app.get("/users/{user_id}/ratings")
def get_user_ratings(user_id: str):
    user_ratings = [r for r in ratings.values() if r.ratee_id == user_id]
    return [
        {
            "rating_id": r.rating_id,
            "trip_id": r.trip_id,
            "stars": r.stars,
            "review_text": r.review_text,
            "review_status": r.review_status.value,
            "created_at": r.created_at,
        }
        for r in user_ratings
    ]
