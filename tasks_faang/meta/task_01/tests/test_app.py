"""Tests for News Feed Ranker."""

import time
import json
import base64
import pytest
from app import NewsFeedRanker, Post, Comment, ContentType, UserRelationship


@pytest.fixture
def ranker() -> NewsFeedRanker:
    r = NewsFeedRanker()
    now = time.time()

    # Add posts with different timestamps
    r.add_post(Post(
        post_id="p1", author_id="alice", content="Old post",
        content_type=ContentType.TEXT, timestamp=now - 7200,  # 2 hours ago
    ))
    r.add_post(Post(
        post_id="p2", author_id="bob", content="Recent post",
        content_type=ContentType.PHOTO, timestamp=now - 60,  # 1 minute ago
    ))
    r.add_post(Post(
        post_id="p3", author_id="carol", content="Medium post",
        content_type=ContentType.VIDEO, timestamp=now - 1800,  # 30 min ago
    ))

    r.set_relationship("viewer", friends={"bob"}, following={"carol"})
    return r


class TestRecencyScoring:
    """Tests for recency-based ranking."""

    def test_recent_posts_rank_higher(self, ranker: NewsFeedRanker):
        """FAILING: Recent posts should rank higher than old posts.

        Bug: Recency decay is inverted — old posts score higher.
        """
        feed = ranker.get_feed("viewer", limit=10)
        # p2 (1 min ago) should come before p1 (2 hours ago)
        ids = [p.post_id for p in feed]
        p2_idx = ids.index("p2")
        p1_idx = ids.index("p1")
        assert p2_idx < p1_idx, "Recent post p2 should rank before old post p1"

    def test_recency_score_decreases_with_age(self, ranker: NewsFeedRanker):
        """FAILING: Recency score should decrease as post gets older."""
        now = time.time()
        score_new = ranker._recency_score(now - 60, now)
        score_old = ranker._recency_score(now - 7200, now)
        assert score_new > score_old, "Newer posts should have higher recency score"


class TestEngagementScoring:
    def test_likes_boost_score(self, ranker: NewsFeedRanker):
        """PASSING: Likes should increase engagement score."""
        post = Post(
            post_id="px", author_id="x", content="test",
            content_type=ContentType.TEXT, timestamp=time.time(),
            likes=["u1", "u2", "u3"],
        )
        score = ranker._engagement_score(post)
        assert score == 3.0

    def test_nested_comments_boost_engagement(self, ranker: NewsFeedRanker):
        """FAILING: Nested (reply) comments should contribute to engagement score.

        Bug: Only top-level comments are counted; replies are ignored.
        """
        now = time.time()
        post = Post(
            post_id="px", author_id="x", content="test",
            content_type=ContentType.TEXT, timestamp=now,
            comments=[
                Comment("c1", "u1", "top level", now),
                Comment("c2", "u2", "reply to c1", now, parent_comment_id="c1"),
                Comment("c3", "u3", "reply to c2", now, parent_comment_id="c2"),
            ],
        )
        score = ranker._engagement_score(post)
        # 1 top-level (c1) * 2.0 = 2.0
        # 2 replies should add extra: reply depth 1 => 2.5, depth 2 => 3.0
        # Total comment score should be > 2.0 (the top-level-only score)
        assert score > 2.0, "Nested comments should increase engagement beyond top-level only"


class TestDeletedPosts:
    def test_deleted_posts_excluded(self, ranker: NewsFeedRanker):
        """FAILING: Deleted posts should not appear in the feed.

        Bug: Deleted posts are still returned.
        """
        ranker.delete_post("p1")
        feed = ranker.get_feed("viewer", limit=10)
        feed_ids = [p.post_id for p in feed]
        assert "p1" not in feed_ids, "Deleted post p1 should not appear in feed"


class TestContentDiversity:
    def test_enforce_diversity_limits_consecutive(self):
        """TODO: Implement content diversity enforcement.

        No more than 2 consecutive posts of the same content type.
        """
        ranker = NewsFeedRanker()
        now = time.time()
        posts = [
            Post(f"p{i}", "author", f"content {i}",
                 ContentType.PHOTO, now - i * 60)
            for i in range(5)
        ]
        # Add a text post that could break up the sequence
        posts.append(Post("p_text", "author", "text post", ContentType.TEXT, now - 150))

        ranker2 = NewsFeedRanker()
        result = ranker2.enforce_diversity(posts, max_consecutive=2)
        # Check no more than 2 consecutive same-type
        for i in range(len(result) - 2):
            if (result[i].content_type == result[i + 1].content_type ==
                    result[i + 2].content_type):
                pytest.fail(
                    f"Three consecutive {result[i].content_type} posts at index {i}"
                )

    def test_enforce_diversity_preserves_all_posts(self):
        """TODO: Diversity enforcement should not drop any posts."""
        ranker = NewsFeedRanker()
        now = time.time()
        posts = [
            Post(f"p{i}", "author", f"content {i}",
                 ContentType.PHOTO if i % 3 == 0 else ContentType.TEXT,
                 now - i * 60)
            for i in range(6)
        ]
        result = ranker.enforce_diversity(posts, max_consecutive=2)
        assert len(result) == len(posts), "Diversity enforcement should keep all posts"


class TestPagination:
    def test_cursor_pagination_first_page(self):
        """TODO: Implement cursor-based pagination — first page."""
        ranker = NewsFeedRanker()
        now = time.time()
        for i in range(20):
            ranker.add_post(Post(
                f"p{i}", "author", f"Post {i}",
                ContentType.TEXT, now - i * 60,
            ))
        ranker.set_relationship("viewer", friends={"author"})

        feed_page1 = ranker.get_feed("viewer", limit=5)
        assert len(feed_page1) == 5

    def test_cursor_pagination_next_page(self):
        """TODO: Implement cursor-based pagination — subsequent pages."""
        ranker = NewsFeedRanker()
        now = time.time()
        for i in range(20):
            ranker.add_post(Post(
                f"p{i}", "author", f"Post {i}",
                ContentType.TEXT, now - i * 60,
            ))
        ranker.set_relationship("viewer", friends={"author"})

        page1 = ranker.get_feed("viewer", limit=5)
        assert len(page1) == 5

        # The get_feed should return a cursor we can use
        # We expect get_feed to accept cursor parameter
        # Encode cursor as base64 of the offset
        cursor = base64.b64encode(json.dumps({"offset": 5}).encode()).decode()
        page2 = ranker.get_feed("viewer", limit=5, cursor=cursor)
        assert len(page2) == 5

        page1_ids = {p.post_id for p in page1}
        page2_ids = {p.post_id for p in page2}
        assert page1_ids.isdisjoint(page2_ids), "Pages should not overlap"
