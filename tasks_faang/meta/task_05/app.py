"""
Post Engagement Tracker
Track likes, comments, shares with analytics and trending detection.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EngagementType(Enum):
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"


@dataclass
class Comment:
    comment_id: str
    post_id: str
    author_id: str
    text: str
    timestamp: float
    parent_comment_id: Optional[str] = None


@dataclass
class EngagementEvent:
    event_type: EngagementType
    post_id: str
    user_id: str
    timestamp: float


@dataclass
class Post:
    post_id: str
    author_id: str
    content: str
    created_at: float
    impressions: int = 0


@dataclass
class Notification:
    post_id: str
    message: str
    milestone: int
    timestamp: float


class EngagementTracker:
    """Tracks engagement (likes, comments, shares) on posts."""

    def __init__(self) -> None:
        self.posts: dict[str, Post] = {}
        self.likes: dict[str, set[str]] = {}  # post_id -> set of user_ids
        self.comments: dict[str, list[Comment]] = {}  # post_id -> list of comments
        self.shares: dict[str, int] = {}  # post_id -> share count
        self.events: list[EngagementEvent] = []
        self.notifications: list[Notification] = []
        self.engagement_counts: dict[str, dict[str, int]] = {}  # post_id -> {type -> count}
        self._lock = threading.Lock()

    def add_post(self, post: Post) -> None:
        self.posts[post.post_id] = post
        self.likes[post.post_id] = set()
        self.comments[post.post_id] = []
        self.shares[post.post_id] = 0
        self.engagement_counts[post.post_id] = {
            "likes": 0, "comments": 0, "shares": 0
        }

    def record_impression(self, post_id: str) -> None:
        if post_id in self.posts:
            self.posts[post_id].impressions += 1

    def toggle_like(self, post_id: str, user_id: str, timestamp: float | None = None) -> bool:
        """Toggle like on a post. Returns True if now liked, False if unliked.

        BUG: Not thread-safe. The check-then-modify pattern has a race condition.
        Also, the engagement count can go negative on unlike.
        """
        if post_id not in self.likes:
            raise ValueError(f"Post {post_id} not found")

        ts = timestamp or time.time()

        # BUG: Race condition — check and modify are not atomic
        # No lock is acquired here
        if user_id in self.likes[post_id]:
            self.likes[post_id].discard(user_id)
            # BUG: Decrements without bounds check — can go negative
            self.engagement_counts[post_id]["likes"] -= 1
            self.events.append(EngagementEvent(
                EngagementType.LIKE, post_id, user_id, ts,
            ))
            return False
        else:
            self.likes[post_id].add(user_id)
            self.engagement_counts[post_id]["likes"] += 1
            self.events.append(EngagementEvent(
                EngagementType.LIKE, post_id, user_id, ts,
            ))
            return True

    def add_comment(self, post_id: str, author_id: str, text: str,
                    parent_comment_id: str | None = None,
                    timestamp: float | None = None) -> Comment:
        """Add a comment (or reply) to a post."""
        if post_id not in self.comments:
            raise ValueError(f"Post {post_id} not found")

        ts = timestamp or time.time()
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            post_id=post_id,
            author_id=author_id,
            text=text,
            timestamp=ts,
            parent_comment_id=parent_comment_id,
        )
        self.comments[post_id].append(comment)
        self.engagement_counts[post_id]["comments"] += 1
        self.events.append(EngagementEvent(
            EngagementType.COMMENT, post_id, author_id, ts,
        ))
        return comment

    def remove_comment(self, post_id: str, comment_id: str) -> bool:
        """Remove a comment from a post."""
        if post_id not in self.comments:
            return False
        for i, c in enumerate(self.comments[post_id]):
            if c.comment_id == comment_id:
                self.comments[post_id].pop(i)
                # BUG: Decrements without checking if it will go below zero
                self.engagement_counts[post_id]["comments"] -= 1
                return True
        return False

    def add_share(self, post_id: str, user_id: str,
                  timestamp: float | None = None) -> None:
        if post_id not in self.shares:
            raise ValueError(f"Post {post_id} not found")
        ts = timestamp or time.time()
        self.shares[post_id] += 1
        self.engagement_counts[post_id]["shares"] += 1
        self.events.append(EngagementEvent(
            EngagementType.SHARE, post_id, user_id, ts,
        ))

    def get_comment_count(self, post_id: str) -> int:
        """Get total comment count including nested replies.

        BUG: Only counts top-level comments via engagement_counts,
        which is incremented correctly, BUT the count can go negative
        from remove_comment bugs. The real issue is the negative count.
        """
        return self.engagement_counts.get(post_id, {}).get("comments", 0)

    def get_like_count(self, post_id: str) -> int:
        """Get the like count for a post. Should never be negative."""
        return self.engagement_counts.get(post_id, {}).get("likes", 0)

    def get_engagement_rate(self, post_id: str) -> float:
        """Calculate engagement rate: (total_interactions / impressions) * 100.

        TODO: Implement engagement rate calculation.
        """
        return 0.0

    def get_trending_posts(self, window_minutes: int = 30,
                           threshold: float = 5.0,
                           now: float | None = None) -> list[str]:
        """Detect trending posts based on engagement velocity.

        A post is trending if interactions_per_minute > threshold
        within the given time window.

        TODO: Implement trending detection.
        """
        return []

    def check_milestones(self, post_id: str) -> list[Notification]:
        """Check if a post hit any engagement milestones (10, 100, 1000 likes).

        Returns list of new notifications generated.

        TODO: Implement milestone notifications.
        """
        return []
