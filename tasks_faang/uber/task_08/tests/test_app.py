"""
Tests for Ride Event Stream Processor.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import time
from app import (
    RideEvent,
    RideRecord,
    EventType,
    RideState,
    rides,
    processed_events,
    metrics,
    process_event,
    ingest_events,
    validate_event,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all state before each test."""
    rides.clear()
    processed_events.clear()
    metrics["total_events"] = 0
    metrics["total_rides"] = 0
    metrics["completed_rides"] = 0
    metrics["cancelled_rides"] = 0
    yield
    rides.clear()
    processed_events.clear()


def _make_event(event_id: str, ride_id: str, event_type: str,
                timestamp: float = None) -> dict:
    return {
        "event_id": event_id,
        "ride_id": ride_id,
        "event_type": event_type,
        "timestamp": timestamp or time.time(),
    }


class TestHappyPath:
    def test_full_ride_lifecycle(self):
        """This test should PASS — normal ride flow."""
        now = time.time()
        events = [
            _make_event("e1", "r1", "RIDE_REQUESTED", now),
            _make_event("e2", "r1", "DRIVER_ACCEPTED", now + 10),
            _make_event("e3", "r1", "RIDE_STARTED", now + 60),
            _make_event("e4", "r1", "RIDE_COMPLETED", now + 600),
        ]
        results = ingest_events(events)

        assert all(r["status"] == "ok" for r in results)
        assert rides["r1"].current_state == RideState.COMPLETED

    def test_ride_cancellation(self):
        """This test should PASS — ride can be cancelled."""
        now = time.time()
        events = [
            _make_event("e1", "r1", "RIDE_REQUESTED", now),
            _make_event("e2", "r1", "RIDE_CANCELLED", now + 30),
        ]
        results = ingest_events(events)
        assert rides["r1"].current_state == RideState.CANCELLED


class TestOutOfOrderEvents:
    def test_out_of_order_events_processed_correctly(self):
        """
        FAILING: Events arriving out of order should be reordered by
        their timestamp before processing. Currently they are processed
        in arrival order.
        """
        now = time.time()
        # Events arrive out of order
        events = [
            _make_event("e1", "r1", "RIDE_REQUESTED", now),
            _make_event("e3", "r1", "RIDE_STARTED", now + 60),   # arrives before ACCEPTED
            _make_event("e2", "r1", "DRIVER_ACCEPTED", now + 10), # arrives late
        ]
        results = ingest_events(events)

        # After reordering, the ride should be in STARTED state
        ride = rides.get("r1")
        assert ride is not None
        assert ride.current_state == RideState.STARTED, (
            f"Expected STARTED but got {ride.current_state.value}"
        )


class TestDuplicateEvents:
    def test_duplicate_event_not_processed_twice(self):
        """
        FAILING: Same event_id submitted twice should only be processed once.
        Currently duplicates are processed, inflating metrics.
        """
        now = time.time()
        events = [
            _make_event("e1", "r1", "RIDE_REQUESTED", now),
            _make_event("e1", "r1", "RIDE_REQUESTED", now),  # duplicate!
        ]
        ingest_events(events)

        assert metrics["total_rides"] == 1, (
            f"Expected 1 ride, got {metrics['total_rides']} — duplicate not caught"
        )
        assert metrics["total_events"] == 1, (
            f"Expected 1 event, got {metrics['total_events']}"
        )


class TestEventValidation:
    def test_missing_required_fields_rejected(self):
        """
        FAILING: Events missing required fields should be rejected.
        Currently validate_event always returns None (valid).
        """
        bad_event = {"event_id": "e1"}  # Missing ride_id, event_type
        error = validate_event(bad_event)
        assert error is not None, "Event with missing fields should fail validation"

    def test_invalid_event_type_rejected(self):
        """
        FAILING: Unknown event types should be rejected at validation.
        """
        bad_event = _make_event("e1", "r1", "INVALID_TYPE")
        # This should be caught by validation before processing
        error = validate_event(bad_event)
        assert error is not None, "Invalid event type should fail validation"

    def test_negative_timestamp_rejected(self):
        """
        FAILING: Negative timestamps should be rejected.
        """
        bad_event = _make_event("e1", "r1", "RIDE_REQUESTED", -100)
        error = validate_event(bad_event)
        assert error is not None, "Negative timestamp should fail validation"


class TestEventAggregation:
    # TODO: Implement rides per hour per zone
    # def test_rides_per_hour(self):
    #     """Should count rides completed per hour."""
    #     pass

    # TODO: Cancellation rate
    # def test_cancellation_rate(self):
    #     """Should calculate the % of rides that were cancelled."""
    #     pass
    pass


class TestDeadLetterQueue:
    # TODO: Implement dead letter queue
    # def test_invalid_event_sent_to_dlq(self):
    #     """Events that fail processing should go to DLQ."""
    #     pass

    # TODO: DLQ retry
    # def test_dlq_retry(self):
    #     """Should be able to retry events from the DLQ."""
    #     pass
    pass
