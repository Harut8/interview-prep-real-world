"""Tests for Notification Aggregator."""

import time
from datetime import datetime, timezone
import pytest
from app import (
    NotificationAggregator, NotificationType, NotificationPreferences,
    Priority, Notification,
)


@pytest.fixture
def aggregator() -> NotificationAggregator:
    return NotificationAggregator()


class TestAggregation:
    def test_same_type_same_target_grouped(self, aggregator: NotificationAggregator):
        """PASSING: Same type + same target should be grouped."""
        for i in range(3):
            aggregator.create_notification(
                "alice", f"user_{i}", NotificationType.LIKE, "post_1",
                f"user_{i} liked your post",
            )
        groups = aggregator.aggregate("alice")
        assert len(groups) == 1
        assert groups[0].count == 3

    def test_different_types_not_grouped(self, aggregator: NotificationAggregator):
        """FAILING: Different notification types on same target should NOT be grouped.

        Bug: Group key missing notification_type — likes and comments merge.
        """
        aggregator.create_notification(
            "alice", "bob", NotificationType.LIKE, "post_1", "bob liked your post",
        )
        aggregator.create_notification(
            "alice", "carol", NotificationType.COMMENT, "post_1",
            "carol commented on your post",
        )
        groups = aggregator.aggregate("alice")
        assert len(groups) == 2, (
            f"Expected 2 groups (like + comment), got {len(groups)}"
        )

    def test_aggregation_summary(self, aggregator: NotificationAggregator):
        """PASSING: Aggregated summary should include count."""
        for i in range(5):
            aggregator.create_notification(
                "alice", f"user_{i}", NotificationType.LIKE, "post_1",
                f"user_{i} liked",
            )
        groups = aggregator.aggregate("alice")
        summary = groups[0].summary()
        assert "4 others" in summary


class TestTimeBucketing:
    def test_same_hour_different_days(self, aggregator: NotificationAggregator):
        """FAILING: Notifications at same hour on different days should be in different buckets.

        Bug: Bucket key only uses hour, not date.
        """
        # 2024-01-01 10:00 UTC
        ts1 = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc).timestamp()
        # 2024-01-02 10:00 UTC (next day, same hour)
        ts2 = datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc).timestamp()

        bucket1 = aggregator._get_time_bucket(ts1)
        bucket2 = aggregator._get_time_bucket(ts2)
        assert bucket1 != bucket2, (
            f"Different days should have different buckets: {bucket1} vs {bucket2}"
        )

    def test_same_day_same_hour(self, aggregator: NotificationAggregator):
        """PASSING: Same hour on same day should be in same bucket."""
        ts1 = datetime(2024, 1, 1, 10, 15, tzinfo=timezone.utc).timestamp()
        ts2 = datetime(2024, 1, 1, 10, 45, tzinfo=timezone.utc).timestamp()
        assert aggregator._get_time_bucket(ts1) == aggregator._get_time_bucket(ts2)


class TestPreferences:
    def test_disabled_type_not_sent(self, aggregator: NotificationAggregator):
        """FAILING: Disabled notification type should not be sent.

        Bug: Preferences are not checked before sending.
        """
        prefs = NotificationPreferences(
            enabled_types={NotificationType.COMMENT, NotificationType.MENTION},
        )
        aggregator.set_preferences("alice", prefs)

        notif = aggregator.create_notification(
            "alice", "bob", NotificationType.LIKE, "post_1", "bob liked",
        )
        result = aggregator.send(notif)
        assert result is False, "LIKE type is disabled, should not be sent"

    def test_enabled_type_sent(self, aggregator: NotificationAggregator):
        """PASSING (once preference check added): Enabled type should be sent."""
        prefs = NotificationPreferences(
            enabled_types={NotificationType.LIKE},
        )
        aggregator.set_preferences("alice", prefs)

        notif = aggregator.create_notification(
            "alice", "bob", NotificationType.LIKE, "post_1", "bob liked",
        )
        result = aggregator.send(notif)
        assert result is True


class TestDigest:
    def test_generate_digest(self, aggregator: NotificationAggregator):
        """TODO: Generate notification digest as list of summary strings."""
        for i in range(3):
            aggregator.create_notification(
                "alice", f"user_{i}", NotificationType.LIKE, "post_1",
                f"user_{i} liked",
            )
        aggregator.create_notification(
            "alice", "bob", NotificationType.COMMENT, "post_1", "bob commented",
        )

        digest = aggregator.generate_digest("alice")
        assert len(digest) >= 2  # at least 2 groups
        assert any("liked" in s.lower() or "like" in s.lower() for s in digest)

    def test_digest_empty_for_no_notifications(self, aggregator: NotificationAggregator):
        """TODO: Empty digest for user with no notifications."""
        digest = aggregator.generate_digest("alice")
        assert digest == []


class TestQuietHours:
    def test_queued_during_quiet_hours(self, aggregator: NotificationAggregator):
        """TODO: Notifications during quiet hours should be queued."""
        prefs = NotificationPreferences(
            quiet_hours_start=22, quiet_hours_end=7,
        )
        aggregator.set_preferences("alice", prefs)

        notif = aggregator.create_notification(
            "alice", "bob", NotificationType.LIKE, "post_1", "liked",
        )
        result = aggregator.send_with_quiet_hours(notif, current_hour=23)
        assert result == "queued"

    def test_delivered_outside_quiet_hours(self, aggregator: NotificationAggregator):
        """TODO: Notifications outside quiet hours should be delivered."""
        prefs = NotificationPreferences(
            quiet_hours_start=22, quiet_hours_end=7,
        )
        aggregator.set_preferences("alice", prefs)

        notif = aggregator.create_notification(
            "alice", "bob", NotificationType.LIKE, "post_1", "liked",
        )
        result = aggregator.send_with_quiet_hours(notif, current_hour=12)
        assert result == "delivered"

    def test_high_priority_bypasses_quiet_hours(self, aggregator: NotificationAggregator):
        """TODO: High priority (security alerts) should bypass quiet hours."""
        prefs = NotificationPreferences(
            quiet_hours_start=22, quiet_hours_end=7,
        )
        aggregator.set_preferences("alice", prefs)

        notif = aggregator.create_notification(
            "alice", "system", NotificationType.SECURITY_ALERT, "alert_1",
            "Suspicious login detected", priority=Priority.HIGH,
        )
        result = aggregator.send_with_quiet_hours(notif, current_hour=23)
        assert result == "delivered"

    def test_flush_queued_after_quiet_hours(self, aggregator: NotificationAggregator):
        """TODO: Queued notifications should be delivered when quiet hours end."""
        prefs = NotificationPreferences(
            quiet_hours_start=22, quiet_hours_end=7,
        )
        aggregator.set_preferences("alice", prefs)

        notif = aggregator.create_notification(
            "alice", "bob", NotificationType.LIKE, "post_1", "liked",
        )
        aggregator.send_with_quiet_hours(notif, current_hour=23)  # queued
        flushed = aggregator.flush_queued("alice", current_hour=8)
        assert len(flushed) == 1
        assert flushed[0].is_delivered is True
