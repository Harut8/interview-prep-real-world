"""Tests for File Activity Feed."""

import pytest
import time
from datetime import datetime, timezone

from app import (
    ActivityFeed,
    ActivityEvent,
    EventType,
    FeedPage,
    WebhookRegistration,
)


@pytest.fixture
def feed() -> ActivityFeed:
    af = ActivityFeed()
    af.register_user("alice", ["/docs/", "/docs/readme.txt"])
    af.register_user("bob", ["/bob_files/"])
    return af


class TestBasicFeed:
    """Tests for basic event recording and retrieval."""

    def test_record_and_retrieve_event(self, feed: ActivityFeed):
        """Recorded events should appear in the actor's feed."""
        feed.record_event(
            EventType.FILE_CREATED,
            "/docs/readme.txt",
            "alice",
            "Alice",
        )

        page = feed.get_feed("alice")
        assert len(page.events) == 1
        assert page.events[0].event_type == EventType.FILE_CREATED

    def test_own_events_always_visible(self, feed: ActivityFeed):
        """Users should always see their own events."""
        feed.record_event(
            EventType.FILE_CREATED,
            "/some/random/path.txt",
            "alice",
            "Alice",
        )

        page = feed.get_feed("alice")
        assert len(page.events) == 1


class TestSharedFolderActivity:
    """Tests for activity in shared folders."""

    # FAILING: BUG #1 - Shared folder events not visible to members
    def test_shared_folder_events_visible_to_all_members(self, feed: ActivityFeed):
        """Events in shared folders should appear for all members."""
        # Share /docs/ folder between alice and bob
        feed.share_path("/docs/", "alice", "bob")

        # Alice creates a file in the shared folder
        feed.record_event(
            EventType.FILE_CREATED,
            "/docs/new_spec.txt",  # New file inside shared folder
            "alice",
            "Alice",
            folder_path="/docs/",
        )

        # Bob should see this event because /docs/ is shared with him
        bob_feed = feed.get_feed("bob")
        shared_events = [e for e in bob_feed.events if e.path == "/docs/new_spec.txt"]
        assert len(shared_events) == 1, (
            "Events in shared folders should be visible to all members"
        )


class TestDeduplication:
    """Tests for event deduplication."""

    # FAILING: BUG #2 - Legitimate repeated actions are deduplicated
    def test_different_actors_same_file_not_deduplicated(self, feed: ActivityFeed):
        """Different users editing the same file should both generate events."""
        feed.record_event(EventType.FILE_EDITED, "/docs/readme.txt", "alice", "Alice")
        feed.record_event(EventType.FILE_EDITED, "/docs/readme.txt", "bob", "Bob")

        # Both events should be recorded
        all_events = feed._events
        edit_events = [e for e in all_events if e.path == "/docs/readme.txt"]
        assert len(edit_events) == 2, (
            f"Expected 2 edit events (one per user), got {len(edit_events)}. "
            f"Different actors' events are being incorrectly deduplicated."
        )

    def test_same_actor_rapid_edits_are_legitimate(self, feed: ActivityFeed):
        """Same user editing a file multiple times should create multiple events."""
        feed.record_event(
            EventType.FILE_EDITED, "/docs/readme.txt", "alice", "Alice",
            details="Added introduction",
        )
        feed.record_event(
            EventType.FILE_EDITED, "/docs/readme.txt", "alice", "Alice",
            details="Fixed typo",
        )

        all_events = feed._events
        edit_events = [
            e for e in all_events
            if e.path == "/docs/readme.txt" and e.event_type == EventType.FILE_EDITED
        ]
        # Both edits are legitimate and should be recorded
        # BUG #2 would filter the second one as "duplicate"
        assert len(edit_events) == 2, (
            "Legitimate repeated edits were incorrectly deduplicated"
        )


class TestPagination:
    """Tests for feed pagination."""

    # FAILING: BUG #3 - Offset-based pagination skips events
    def test_pagination_stable_with_new_events(self, feed: ActivityFeed):
        """Pagination should not skip events when new events arrive between pages."""
        # Record 10 events
        for i in range(10):
            path = f"/docs/file_{i}.txt"
            feed.register_user("alice", [path])
            feed.record_event(EventType.FILE_CREATED, path, "alice", "Alice")
            time.sleep(0.01)  # Ensure unique timestamps for dedup

        # Get first page (5 events)
        page1 = feed.get_feed("alice", page_size=5)
        assert len(page1.events) == 5
        page1_ids = {e.event_id for e in page1.events}

        # New events arrive before fetching page 2
        for i in range(3):
            path = f"/docs/new_file_{i}.txt"
            feed.register_user("alice", [path])
            feed.record_event(EventType.FILE_CREATED, path, "alice", "Alice")
            time.sleep(0.01)

        # Get second page using cursor from first page
        page2 = feed.get_feed("alice", cursor=page1.cursor, page_size=5)
        page2_ids = {e.event_id for e in page2.events}

        # No events should be in both pages (no repeats)
        overlap = page1_ids & page2_ids
        assert len(overlap) == 0, f"Events repeated across pages: {overlap}"

        # Collect all events across all pages
        all_seen = page1_ids | page2_ids
        remaining_cursor = page2.cursor
        while page2.has_more:
            page2 = feed.get_feed("alice", cursor=remaining_cursor, page_size=5)
            for e in page2.events:
                assert e.event_id not in all_seen, f"Event {e.event_id} seen twice"
                all_seen.add(e.event_id)
            remaining_cursor = page2.cursor


class TestWebhooks:
    """Tests for webhook notifications."""

    def test_webhook_triggered_on_matching_event(self, feed: ActivityFeed):
        """Webhook should fire for matching event types."""
        received: list[ActivityEvent] = []
        feed.register_webhook("alice", [EventType.FILE_DELETED], lambda e: received.append(e))

        feed.record_event(EventType.FILE_CREATED, "/docs/x.txt", "alice", "Alice")
        feed.record_event(EventType.FILE_DELETED, "/docs/x.txt", "alice", "Alice")

        assert len(received) == 1
        assert received[0].event_type == EventType.FILE_DELETED

    # TODO: Implement activity filtering by type
    def test_feed_filtered_by_event_type(self, feed: ActivityFeed):
        """Feed should support filtering by event type."""
        feed.record_event(EventType.FILE_CREATED, "/docs/a.txt", "alice", "Alice")
        time.sleep(0.01)
        feed.record_event(EventType.FILE_EDITED, "/docs/a.txt", "alice", "Alice")
        time.sleep(0.01)
        feed.record_event(EventType.FILE_DELETED, "/docs/a.txt", "alice", "Alice")

        page = feed.get_feed("alice", event_types=[EventType.FILE_EDITED])
        assert all(e.event_type == EventType.FILE_EDITED for e in page.events)

    # TODO: Implement event rollup
    def test_event_rollup(self, feed: ActivityFeed):
        """Similar events should be rolled up into summaries."""
        pytest.skip("TODO: Implement event rollup (batch similar events)")
