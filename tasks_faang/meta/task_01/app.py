"""
News Feed Ranker Service
Ranks and serves personalized news feed posts for users.
"""

from __future__ import annotations

import math
import time
import base64
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ContentType(Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    LINK = "link"
    EVENT = "event"


@dataclass
class Comment:
    comment_id: str
    author_id: str
    text: str
    timestamp: float
    parent_comment_id: Optional[str] = None  # None means top-level


@dataclass
class Post:
    post_id: str
    author_id: str
    content: str
    content_type: ContentType
    timestamp: float
    likes: list[str] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    shares: int = 0
    is_deleted: bool = False


@dataclass
class UserRelationship:
    user_id: str
    friends: set[str] = field(default_factory=set)
    following: set[str] = field(default_factory=set)


class NewsFeedRanker:
    """Ranks posts for a user's personalized news feed."""

    RECENCY_HALF_LIFE = 3600  # 1 hour half-life for recency decay
    FRIEND_BOOST = 2.0
    FOLLOW_BOOST = 1.5
    ENGAGEMENT_WEIGHT = 0.3
    RECENCY_WEIGHT = 0.5
    RELATIONSHIP_WEIGHT = 0.2

    def __init__(self) -> None:
        self.posts: dict[str, Post] = {}
        self.relationships: dict[str, UserRelationship] = {}

    def add_post(self, post: Post) -> None:
        self.posts[post.post_id] = post

    def delete_post(self, post_id: str) -> None:
        if post_id in self.posts:
            self.posts[post_id].is_deleted = True

    def set_relationship(self, user_id: str, friends: set[str] | None = None,
                         following: set[str] | None = None) -> None:
        if user_id not in self.relationships:
            self.relationships[user_id] = UserRelationship(user_id=user_id)
        rel = self.relationships[user_id]
        if friends is not None:
            rel.friends = friends
        if following is not None:
            rel.following = following

    def _recency_score(self, post_timestamp: float, now: float) -> float:
        """Calculate recency score. More recent posts should score higher.

        Uses exponential decay with a half-life.
        """
        age_seconds = now - post_timestamp
        # BUG: The decay function is inverted — older posts get HIGHER scores.
        # The exponent should be negative to penalize age.
        decay = math.pow(2, age_seconds / self.RECENCY_HALF_LIFE)
        return decay

    def _engagement_score(self, post: Post) -> float:
        """Calculate engagement score based on likes, comments, and shares.

        Deeper comment threads indicate higher engagement.
        """
        like_score = len(post.likes) * 1.0
        share_score = post.shares * 3.0

        # BUG: Only counts top-level comments, ignores nested replies.
        # Should weight nested comments (replies) more to reflect deeper engagement.
        top_level_comments = [c for c in post.comments if c.parent_comment_id is None]
        comment_score = len(top_level_comments) * 2.0

        return like_score + comment_score + share_score

    def _relationship_score(self, viewer_id: str, author_id: str) -> float:
        """Score based on viewer's relationship with post author."""
        rel = self.relationships.get(viewer_id)
        if rel is None:
            return 0.0
        if author_id in rel.friends:
            return self.FRIEND_BOOST
        if author_id in rel.following:
            return self.FOLLOW_BOOST
        return 0.0

    def _score_post(self, post: Post, viewer_id: str, now: float) -> float:
        """Compute total relevance score for a post."""
        recency = self._recency_score(post.timestamp, now)
        engagement = self._engagement_score(post)
        relationship = self._relationship_score(viewer_id, post.author_id)

        total = (
            self.RECENCY_WEIGHT * recency
            + self.ENGAGEMENT_WEIGHT * engagement
            + self.RELATIONSHIP_WEIGHT * relationship
        )
        return total

    def get_feed(self, user_id: str, limit: int = 10, cursor: str | None = None) -> list[Post]:
        """Return ranked feed for the user.

        Args:
            user_id: The viewer requesting their feed.
            limit: Maximum number of posts to return.
            cursor: Opaque cursor for pagination (not yet implemented).

        Returns:
            List of posts ranked by relevance score (highest first).
        """
        now = time.time()

        # BUG: Deleted posts are not filtered out.
        # All posts are considered, including those with is_deleted=True.
        candidates = [
            p for p in self.posts.values()
            if p.author_id != user_id
        ]

        scored = [(self._score_post(p, user_id, now), p) for p in candidates]
        scored.sort(key=lambda x: x[0], reverse=True)

        ranked_posts = [p for _, p in scored]

        # TODO: Implement cursor-based pagination
        # For now, just return first `limit` posts
        return ranked_posts[:limit]

    def enforce_diversity(self, posts: list[Post], max_consecutive: int = 2) -> list[Post]:
        """Enforce content type diversity in the feed.

        No more than `max_consecutive` posts of the same content type in a row.
        Reorder minimally while preserving relative rank as much as possible.

        TODO: Implement this method.
        """
        return posts
