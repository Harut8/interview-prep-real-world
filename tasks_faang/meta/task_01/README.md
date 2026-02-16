# Task 01: News Feed Ranker

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are working on Meta's News Feed ranking service. The service ranks posts for a
user's feed based on recency, engagement, author relationship, and content type.
Posts are scored and returned in ranked order.

## Existing Codebase

The `app.py` file contains a `NewsFeedRanker` that:
- Stores posts from various authors
- Computes a relevance score per post for a given viewer
- Returns a ranked feed for any user
- Supports friendship/follow relationships for boosting

## Known Bugs (3-4 to find and fix)

1. **Recency score is inverted** — Older posts are ranking higher than newer posts.
   The decay function rewards age instead of penalizing it.
2. **Comment depth ignored in interaction weight** — The interaction scoring only
   counts top-level comments, not nested replies. Deeper engagement should boost
   a post's score.
3. **Deleted posts appear in feed** — Posts marked as deleted (`is_deleted=True`)
   still show up in the ranked feed results.

## Features to Implement

1. **Content Diversity Enforcement** — No more than 2 consecutive posts from the
   same content type (e.g., "photo", "video", "text") in the final feed. Reorder
   as needed while preserving relative rank order as much as possible.
2. **Cursor-based Pagination** — Implement `get_feed(user_id, cursor=None, limit=10)`
   that supports cursor-based pagination. The cursor should encode the position in
   the ranked feed so subsequent calls return the next page.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, and some
  are TODOs for the new features.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
