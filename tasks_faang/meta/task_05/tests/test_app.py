"""Tests for Post Engagement Tracker."""

import time
import threading
import pytest
from app import EngagementTracker, Post, EngagementType


@pytest.fixture
def tracker() -> EngagementTracker:
    t = EngagementTracker()
    now = time.time()
    t.add_post(Post("p1", "author1", "Test post", now))
    t.add_post(Post("p2", "author2", "Another post", now))
    return t


class TestLikeToggle:
    def test_like_and_unlike(self, tracker: EngagementTracker):
        """PASSING: Basic like/unlike toggle should work."""
        assert tracker.toggle_like("p1", "user1") is True  # like
        assert tracker.get_like_count("p1") == 1
        assert tracker.toggle_like("p1", "user1") is False  # unlike
        assert tracker.get_like_count("p1") == 0

    def test_like_count_never_negative(self, tracker: EngagementTracker):
        """FAILING: Like count should never go below zero.

        Bug: Rapid unlike when count is already 0 can make it negative.
        """
        # Like then unlike
        tracker.toggle_like("p1", "user1")
        tracker.toggle_like("p1", "user1")
        assert tracker.get_like_count("p1") == 0

        # Force another unlike attempt by manipulating state
        # Simulate race: user appears in set but count is 0
        tracker.likes["p1"].add("user1")
        tracker.toggle_like("p1", "user1")  # unlike
        count = tracker.get_like_count("p1")
        assert count >= 0, f"Like count should never be negative, got {count}"

    def test_concurrent_likes_consistent(self, tracker: EngagementTracker):
        """FAILING: Concurrent like toggles should maintain consistent state.

        Bug: toggle_like is not thread-safe.
        """
        errors = []

        def like_many():
            try:
                for i in range(50):
                    tracker.toggle_like("p1", f"user_{threading.current_thread().name}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=like_many, name=f"t{i}") for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent likes: {errors}"
        # After all operations, like count should equal number of users in the set
        actual_likes = len(tracker.likes["p1"])
        reported_count = tracker.get_like_count("p1")
        assert actual_likes == reported_count, (
            f"Actual likes ({actual_likes}) != reported count ({reported_count})"
        )


class TestComments:
    def test_add_nested_comments(self, tracker: EngagementTracker):
        """PASSING: Adding nested comments should work."""
        c1 = tracker.add_comment("p1", "user1", "Top level")
        c2 = tracker.add_comment("p1", "user2", "Reply", parent_comment_id=c1.comment_id)
        assert len(tracker.comments["p1"]) == 2

    def test_total_comment_count_includes_replies(self, tracker: EngagementTracker):
        """PASSING (count tracks all adds): Comment count should include replies."""
        c1 = tracker.add_comment("p1", "user1", "Top level")
        tracker.add_comment("p1", "user2", "Reply 1", parent_comment_id=c1.comment_id)
        tracker.add_comment("p1", "user3", "Reply 2", parent_comment_id=c1.comment_id)
        assert tracker.get_comment_count("p1") == 3

    def test_remove_comment_count_not_negative(self, tracker: EngagementTracker):
        """FAILING: Removing comments should not make count go negative.

        Bug: No bounds checking on decrement.
        """
        c1 = tracker.add_comment("p1", "user1", "Comment")
        tracker.remove_comment("p1", c1.comment_id)
        assert tracker.get_comment_count("p1") == 0
        # Try removing again (should not succeed, but count shouldn't go negative)
        tracker.remove_comment("p1", "nonexistent")
        count = tracker.get_comment_count("p1")
        assert count >= 0, f"Comment count should never be negative, got {count}"


class TestEngagementRate:
    def test_engagement_rate_calculation(self, tracker: EngagementTracker):
        """TODO: Engagement rate = (interactions / impressions) * 100."""
        # Record impressions
        for _ in range(100):
            tracker.record_impression("p1")
        # 5 likes + 3 comments + 2 shares = 10 interactions
        for i in range(5):
            tracker.toggle_like("p1", f"liker_{i}")
        for i in range(3):
            tracker.add_comment("p1", f"commenter_{i}", f"Comment {i}")
        for i in range(2):
            tracker.add_share("p1", f"sharer_{i}")

        rate = tracker.get_engagement_rate("p1")
        assert rate == pytest.approx(10.0, abs=0.1), (
            f"Expected 10.0% engagement rate, got {rate}"
        )

    def test_engagement_rate_zero_impressions(self, tracker: EngagementTracker):
        """TODO: Engagement rate with zero impressions should return 0.0."""
        tracker.toggle_like("p1", "user1")
        rate = tracker.get_engagement_rate("p1")
        assert rate == 0.0


class TestTrending:
    def test_trending_detection(self, tracker: EngagementTracker):
        """TODO: Post with high engagement velocity should be detected as trending."""
        now = time.time()
        # Generate 20 events in the last 2 minutes
        for i in range(20):
            tracker.toggle_like("p1", f"user_{i}", timestamp=now - (i * 5))

        trending = tracker.get_trending_posts(
            window_minutes=5, threshold=3.0, now=now
        )
        assert "p1" in trending

    def test_not_trending_low_velocity(self, tracker: EngagementTracker):
        """TODO: Post with low engagement velocity should not be trending."""
        now = time.time()
        # Only 1 event in 30 minutes
        tracker.toggle_like("p1", "user1", timestamp=now - 100)
        trending = tracker.get_trending_posts(
            window_minutes=30, threshold=5.0, now=now
        )
        assert "p1" not in trending


class TestMilestones:
    def test_milestone_at_10_likes(self, tracker: EngagementTracker):
        """TODO: Hitting 10 likes should generate a notification."""
        for i in range(10):
            tracker.toggle_like("p1", f"user_{i}")

        notifications = tracker.check_milestones("p1")
        milestones = [n.milestone for n in notifications]
        assert 10 in milestones

    def test_no_duplicate_milestone_notifications(self, tracker: EngagementTracker):
        """TODO: Same milestone should not generate duplicate notifications."""
        for i in range(10):
            tracker.toggle_like("p1", f"user_{i}")
        tracker.check_milestones("p1")
        # Check again — should not duplicate
        notifications = tracker.check_milestones("p1")
        milestones_10 = [n for n in notifications if n.milestone == 10]
        assert len(milestones_10) == 0, "Milestone 10 should not fire again"
