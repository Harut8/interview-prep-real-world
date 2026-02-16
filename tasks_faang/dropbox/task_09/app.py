"""
File Activity Feed - Track and display file/folder activity events.

Simulates Dropbox-style activity feed with event tracking,
pagination, deduplication, and notification support.
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional, Callable


class EventType(Enum):
    FILE_CREATED = auto()
    FILE_EDITED = auto()
    FILE_DELETED = auto()
    FILE_RENAMED = auto()
    FILE_MOVED = auto()
    FILE_SHARED = auto()
    FILE_UNSHARED = auto()
    FOLDER_CREATED = auto()
    FOLDER_DELETED = auto()
    COMMENT_ADDED = auto()


@dataclass
class ActivityEvent:
    """A single activity event."""
    event_id: str
    event_type: EventType
    path: str
    actor_id: str
    actor_name: str
    timestamp: datetime
    details: str = ""
    folder_path: Optional[str] = None  # Parent folder for inheritance


@dataclass
class FeedPage:
    """A page of activity feed results."""
    events: list[ActivityEvent]
    cursor: str  # Opaque cursor for next page
    has_more: bool
    total_count: int


@dataclass
class WebhookRegistration:
    """A registered webhook for event notifications."""
    webhook_id: str
    user_id: str
    event_types: list[EventType]
    callback: Callable[[ActivityEvent], None]


class ActivityFeed:
    """
    File activity feed system.

    Records events, provides paginated feeds per user, and
    supports filtering, rollup, and webhook notifications.
    """

    # Deduplication window in seconds
    DEDUP_WINDOW_SECONDS = 300  # 5 minutes

    def __init__(self):
        # All events in chronological order (newest first)
        self._events: list[ActivityEvent] = []
        # user_id -> set of paths they can see events for
        self._user_visible_paths: dict[str, set[str]] = {}
        # path -> set of user_ids who share this path
        self._shared_paths: dict[str, set[str]] = {}
        # Registered webhooks
        self._webhooks: list[WebhookRegistration] = []

    def register_user(self, user_id: str, owned_paths: list[str] | None = None) -> None:
        """Register a user with their initially visible paths."""
        if user_id not in self._user_visible_paths:
            self._user_visible_paths[user_id] = set()
        if owned_paths:
            self._user_visible_paths[user_id].update(owned_paths)

    def share_path(self, path: str, owner_id: str, shared_with: str) -> None:
        """Record that a path is shared between users."""
        if path not in self._shared_paths:
            self._shared_paths[path] = set()
        self._shared_paths[path].add(owner_id)
        self._shared_paths[path].add(shared_with)

        # Add to visible paths
        if shared_with not in self._user_visible_paths:
            self._user_visible_paths[shared_with] = set()
        self._user_visible_paths[shared_with].add(path)

    def record_event(
        self,
        event_type: EventType,
        path: str,
        actor_id: str,
        actor_name: str,
        details: str = "",
        folder_path: str | None = None,
    ) -> ActivityEvent:
        """
        Record a new activity event.

        BUG #2: Deduplication is too aggressive. Events with the same type
        and path within the dedup window are considered duplicates, even
        if they are legitimate repeated actions (e.g., editing twice).
        """
        event = ActivityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            path=path,
            actor_id=actor_id,
            actor_name=actor_name,
            timestamp=datetime.now(timezone.utc),
            details=details,
            folder_path=folder_path,
        )

        # BUG #2: Over-aggressive deduplication
        # Filters out events with same type + path within the time window,
        # even if they are by different actors or are legitimately repeated
        if self._is_duplicate(event):
            return event  # Silently drops the event

        # Insert at the beginning (newest first)
        self._events.insert(0, event)

        # Notify webhooks
        self._notify_webhooks(event)

        return event

    def _is_duplicate(self, event: ActivityEvent) -> bool:
        """
        Check if an event is a duplicate.

        BUG #2: Only checks event_type and path, ignoring actor_id
        and other distinguishing fields. Two different users editing
        the same file within 5 minutes is NOT a duplicate, but this
        treats it as one.
        """
        cutoff = time.time() - self.DEDUP_WINDOW_SECONDS

        for existing in self._events:
            if existing.timestamp.timestamp() < cutoff:
                break  # Events are sorted newest first, so we can stop

            # BUG #2: Doesn't check actor_id - different actors' events
            # are treated as duplicates if type and path match
            if (existing.event_type == event.event_type
                    and existing.path == event.path):
                return True

        return False

    def get_feed(
        self,
        user_id: str,
        cursor: str | None = None,
        page_size: int = 20,
        event_types: list[EventType] | None = None,
    ) -> FeedPage:
        """
        Get paginated activity feed for a user.

        BUG #1: Only shows events for paths directly in the user's
        visible paths. Does NOT include events for paths in shared
        folders (events where folder_path is shared but path itself isn't).

        BUG #3: Uses integer offset as cursor. When new events are
        inserted at the top between page requests, the offset shifts
        and events are skipped.
        """
        # Determine starting offset from cursor
        # BUG #3: Offset-based pagination breaks when new events arrive
        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except ValueError:
                offset = 0

        # Get events visible to this user
        visible_paths = self._user_visible_paths.get(user_id, set())
        visible_events: list[ActivityEvent] = []

        for event in self._events:
            # BUG #1: Only checks if event.path is in visible_paths.
            # Doesn't check if event.folder_path is in visible_paths
            # or shared_paths. Events in shared folders are missed.
            if event.path in visible_paths or event.actor_id == user_id:
                if event_types is None or event.event_type in event_types:
                    visible_events.append(event)

        # Apply pagination
        total = len(visible_events)
        page_events = visible_events[offset:offset + page_size]
        has_more = (offset + page_size) < total

        # BUG #3: Next cursor is just offset + page_size (integer-based)
        next_cursor = str(offset + page_size)

        return FeedPage(
            events=page_events,
            cursor=next_cursor,
            has_more=has_more,
            total_count=total,
        )

    def register_webhook(
        self,
        user_id: str,
        event_types: list[EventType],
        callback: Callable[[ActivityEvent], None],
    ) -> WebhookRegistration:
        """Register a webhook for event notifications."""
        registration = WebhookRegistration(
            webhook_id=str(uuid.uuid4()),
            user_id=user_id,
            event_types=event_types,
            callback=callback,
        )
        self._webhooks.append(registration)
        return registration

    def _notify_webhooks(self, event: ActivityEvent) -> None:
        """Send event to registered webhooks."""
        for webhook in self._webhooks:
            if event.event_type in webhook.event_types:
                try:
                    webhook.callback(event)
                except Exception:
                    pass  # Don't let webhook failures affect event recording

    def rollup_events(
        self,
        events: list[ActivityEvent],
        window_seconds: int = 3600,
    ) -> list[dict]:
        """
        Roll up similar events into summaries.

        Stub - needs implementation.
        """
        # TODO: Implement event rollup
        return [{"event": e, "count": 1} for e in events]
