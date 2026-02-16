"""
Notification Aggregator
Aggregate, batch, and deliver notifications with user preferences.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class NotificationType(Enum):
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    FRIEND_REQUEST = "friend_request"
    MENTION = "mention"
    SECURITY_ALERT = "security_alert"


class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class Notification:
    notification_id: str
    recipient_id: str
    sender_id: str
    notification_type: NotificationType
    target_id: str  # e.g., post_id
    message: str
    timestamp: float
    priority: Priority = Priority.NORMAL
    is_read: bool = False
    is_delivered: bool = False


@dataclass
class AggregatedNotification:
    """A group of similar notifications."""
    group_key: str
    notification_type: NotificationType
    target_id: str
    notifications: list[Notification] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.notifications)

    def summary(self) -> str:
        if self.count == 0:
            return ""
        senders = [n.sender_id for n in self.notifications]
        if self.count == 1:
            return f"{senders[0]} {self.notification_type.value}d your post"
        return (
            f"{senders[0]} and {self.count - 1} others "
            f"{self.notification_type.value}d your post"
        )


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    enabled_types: set[NotificationType] = field(
        default_factory=lambda: set(NotificationType)
    )
    quiet_hours_start: Optional[int] = None  # hour (0-23)
    quiet_hours_end: Optional[int] = None  # hour (0-23)
    email_enabled: bool = True
    push_enabled: bool = True


class NotificationAggregator:
    """Aggregates and delivers notifications with preferences."""

    def __init__(self) -> None:
        self.notifications: list[Notification] = []
        self.preferences: dict[str, NotificationPreferences] = {}
        self.delivered: list[Notification] = []
        self.queued: list[Notification] = []  # queued during quiet hours

    def set_preferences(self, user_id: str, prefs: NotificationPreferences) -> None:
        self.preferences[user_id] = prefs

    def create_notification(
        self,
        recipient_id: str,
        sender_id: str,
        notification_type: NotificationType,
        target_id: str,
        message: str,
        timestamp: float | None = None,
        priority: Priority = Priority.NORMAL,
    ) -> Notification:
        notif = Notification(
            notification_id=str(uuid.uuid4()),
            recipient_id=recipient_id,
            sender_id=sender_id,
            notification_type=notification_type,
            target_id=target_id,
            message=message,
            timestamp=timestamp or time.time(),
            priority=priority,
        )
        self.notifications.append(notif)
        return notif

    def _make_group_key(self, notification: Notification) -> str:
        """Create grouping key for aggregation.

        BUG: Does not include notification_type in the key.
        Likes and comments on the same post get grouped together.
        """
        # BUG: Missing notification_type in group key
        return f"{notification.recipient_id}:{notification.target_id}"

    def _get_time_bucket(self, timestamp: float) -> str:
        """Get time bucket string for a notification timestamp.

        Groups notifications into hourly buckets.

        BUG: Uses simple integer division on hours, which doesn't account
        for day boundaries. Notifications at 23:30 and 00:30 could end up
        in buckets that incorrectly merge across midnight.
        """
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        # BUG: Only uses hour, ignoring the date. Two notifications on
        # different days at the same hour get the same bucket.
        return f"bucket_{dt.hour}"

    def aggregate(self, user_id: str) -> list[AggregatedNotification]:
        """Aggregate notifications for a user into groups."""
        user_notifs = [n for n in self.notifications
                       if n.recipient_id == user_id and not n.is_read]

        groups: dict[str, AggregatedNotification] = {}
        for notif in user_notifs:
            key = self._make_group_key(notif)
            if key not in groups:
                groups[key] = AggregatedNotification(
                    group_key=key,
                    notification_type=notif.notification_type,
                    target_id=notif.target_id,
                )
            groups[key].notifications.append(notif)

        return list(groups.values())

    def send(self, notification: Notification, current_hour: int | None = None) -> bool:
        """Deliver a notification to the user.

        BUG: Does not check user preferences before sending.
        Should skip if notification type is disabled in preferences.
        """
        # BUG: No preference check — sends everything
        notification.is_delivered = True
        self.delivered.append(notification)
        return True

    def _is_quiet_hours(self, user_id: str, current_hour: int) -> bool:
        """Check if current time is within user's quiet hours."""
        prefs = self.preferences.get(user_id)
        if prefs is None or prefs.quiet_hours_start is None:
            return False
        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end
        if end is None:
            return False
        if start < end:
            return start <= current_hour < end
        else:
            # Wraps around midnight (e.g., 22:00 to 07:00)
            return current_hour >= start or current_hour < end

    def generate_digest(self, user_id: str) -> list[str]:
        """Generate notification digest — list of aggregated summary strings.

        TODO: Implement digest generation.
        """
        return []

    def send_with_quiet_hours(self, notification: Notification,
                              current_hour: int) -> str:
        """Send notification respecting quiet hours.

        Returns "delivered", "queued", or "skipped".

        TODO: Implement quiet hours support.
        """
        return "delivered"

    def flush_queued(self, user_id: str, current_hour: int) -> list[Notification]:
        """Deliver queued notifications if quiet hours are over.

        TODO: Implement queue flushing.
        """
        return []
