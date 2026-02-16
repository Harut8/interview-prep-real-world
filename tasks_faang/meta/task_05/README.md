# Task 05: Post Engagement Tracker

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Post Engagement Tracker. The system tracks likes, comments,
and shares on posts, computes engagement analytics, and detects trending content.

## Existing Codebase

The `app.py` file contains an `EngagementTracker` that:
- Tracks likes (with toggle), comments (nested), and shares
- Computes engagement counts per post
- Stores engagement events with timestamps

## Known Bugs (3-4 to find and fix)

1. **Like/unlike toggle race condition** — The toggle_like method checks and
   modifies the liked set non-atomically. With concurrent-like simulation (calling
   toggle rapidly), state becomes inconsistent.
2. **Engagement count can go negative** — When unliking or removing comments, the
   count can drop below zero due to missing bounds checking.
3. **Nested comment count is wrong** — The total comment count only counts top-level
   comments, missing nested replies.

## Features to Implement

1. **Engagement Rate Calculation** — Calculate engagement rate as
   (total_interactions / impressions) * 100 for a post.
2. **Trending Detection** — Detect posts that are trending based on engagement
   velocity (interactions per minute over last N minutes exceeding a threshold).
3. **Engagement Notifications** — Generate notification events when posts hit
   engagement milestones (e.g., 10, 100, 1000 likes).

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
