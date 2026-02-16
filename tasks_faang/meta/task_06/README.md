# Task 06: User Privacy Settings Manager

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Privacy Settings Manager. It manages complex privacy rules
for profile visibility, content access, and audience targeting. Users can control
who sees their posts, profile info, and friend lists.

## Existing Codebase

The `app.py` file contains a `PrivacyManager` that:
- Manages per-user privacy settings for various fields
- Supports audience levels: PUBLIC, FRIENDS, FRIENDS_OF_FRIENDS, ONLY_ME
- Checks whether a viewer can access a user's content
- Supports group-level privacy inheritance

## Known Bugs (3-4 to find and fix)

1. **Privacy inheritance from group settings is broken** — When a user belongs to
   a group with privacy settings, the group settings should serve as defaults that
   user settings can override. Currently, group settings are ignored entirely.
2. **"Friends of friends" check doesn't work** — The FRIENDS_OF_FRIENDS audience
   check fails because it only checks direct friends, not second-degree connections.
3. **Blocking doesn't hide old content** — When user A blocks user B, B should
   not be able to see any of A's content. Currently, the block check is only
   applied to new content, not existing content access checks.

## Features to Implement

1. **Privacy Presets** — Predefined privacy configurations (e.g., "strict",
   "moderate", "open") that users can apply as a whole.
2. **Data Export (GDPR)** — Export all of a user's data (profile, posts, settings)
   in a structured dictionary format.
3. **Audience Selector** — Given a post's audience setting, return the list of
   user IDs who can see it.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
