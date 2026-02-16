"""
Tests for Rating & Review System.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import time
from app import (
    Trip,
    Rating,
    UserProfile,
    RaterType,
    ReviewStatus,
    trips,
    ratings,
    profiles,
    average_cache,
    submit_rating,
    calculate_average_rating,
    is_within_rating_window,
    get_cached_average,
    RATING_WINDOW_SECONDS,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all state before each test."""
    trips.clear()
    ratings.clear()
    profiles.clear()
    average_cache.clear()
    yield
    trips.clear()
    ratings.clear()
    profiles.clear()
    average_cache.clear()


def _create_trip(trip_id: str = "t1", completed_at: float = None) -> Trip:
    if completed_at is None:
        completed_at = time.time()
    trip = Trip(
        trip_id=trip_id,
        rider_id="rider1",
        driver_id="driver1",
        completed_at=completed_at,
    )
    trips[trip_id] = trip
    # Set up profiles with ride counts
    for uid in ["rider1", "driver1"]:
        if uid not in profiles:
            profiles[uid] = UserProfile(user_id=uid, user_type=RaterType.RIDER)
        profiles[uid].total_rides += 1
    return trip


class TestRatingWindow:
    def test_within_window_allows_rating(self):
        """
        FAILING: Rating within 24h window should be allowed.
        Bug: is_within_rating_window is inverted.
        """
        trip = _create_trip(completed_at=time.time() - 3600)  # 1 hour ago
        # Should be within window
        assert is_within_rating_window(trip) is True

    def test_expired_window_rejects_rating(self):
        """
        FAILING: Rating after 24h should be rejected.
        Bug: window check is inverted.
        """
        trip = _create_trip(
            completed_at=time.time() - RATING_WINDOW_SECONDS - 3600
        )  # 25 hours ago
        assert is_within_rating_window(trip) is False


class TestAverageRating:
    def test_average_single_rating(self):
        """This test should PASS — single rating is the average."""
        _create_trip("t1")
        submit_rating("t1", "rider1", RaterType.RIDER, 4)
        avg = calculate_average_rating("driver1")
        assert avg == pytest.approx(4.0)

    def test_average_with_unrated_rides(self):
        """
        FAILING: Average should divide by ratings received, not total rides.
        Driver with 3 rides but only 2 ratings: avg should be sum/2, not sum/3.
        """
        # Create 3 trips (driver does 3 rides)
        for i in range(3):
            _create_trip(f"t{i}")

        # Only 2 ratings submitted
        submit_rating("t0", "rider1", RaterType.RIDER, 5)
        submit_rating("t1", "rider1", RaterType.RIDER, 4)

        avg = calculate_average_rating("driver1")
        # Should be (5+4)/2 = 4.5, not (5+4)/3 = 3.0
        assert avg == pytest.approx(4.5), (
            f"Average {avg} should be 4.5 (dividing by ratings count, not rides)"
        )


class TestCacheInvalidation:
    def test_new_rating_invalidates_cache(self):
        """
        FAILING: After a new rating, the cached average should be invalidated.
        Currently the cache retains the old value.
        """
        _create_trip("t1")
        _create_trip("t2")

        submit_rating("t1", "rider1", RaterType.RIDER, 5)

        # Prime the cache
        from app import CachedAverage
        avg = calculate_average_rating("driver1")
        average_cache["driver1"] = CachedAverage(
            user_id="driver1", average=avg
        )

        # Submit another rating that changes the average
        submit_rating("t2", "rider1", RaterType.RIDER, 3)

        # Cache should be invalidated — get_cached_average should return None
        cached = get_cached_average("driver1")
        assert cached is None or cached != 5.0, (
            "Cache was not invalidated after new rating"
        )


class TestDuplicateRating:
    def test_cannot_rate_same_trip_twice(self):
        """This test should PASS — duplicate rating raises error."""
        _create_trip("t1")
        submit_rating("t1", "rider1", RaterType.RIDER, 4)
        with pytest.raises(ValueError, match="Already rated"):
            submit_rating("t1", "rider1", RaterType.RIDER, 5)


class TestProfanityFilter:
    # TODO: Implement review moderation with profanity filter
    # def test_profanity_flagged_for_review(self):
    #     """Review with bad words should be stored but marked pending_review."""
    #     pass

    # TODO: Clean reviews auto-approved
    # def test_clean_review_auto_approved(self):
    #     """Review without bad words should be automatically approved."""
    #     pass
    pass


class TestRatingTrends:
    # TODO: Implement rating trends over time
    # def test_weekly_rating_trend(self):
    #     """Should return average rating per week over a period."""
    #     pass

    # TODO: Monthly trend
    # def test_monthly_rating_trend(self):
    #     """Should return average rating per month."""
    #     pass
    pass
