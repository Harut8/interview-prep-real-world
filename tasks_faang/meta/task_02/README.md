# Task 02: Social Graph Service

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Social Graph Service. It manages friend connections,
computes friend suggestions, and supports graph queries like mutual friends and
degrees of separation.

## Existing Codebase

The `app.py` file contains a `SocialGraph` that:
- Stores bidirectional friendships between users
- Computes mutual friends between two users
- Finds friend-of-friend connections
- Supports friend removal

## Known Bugs (3-4 to find and fix)

1. **Friend-of-friend query infinite loop** — The `get_friends_of_friends` method
   doesn't track visited nodes, causing cycles that lead to infinite loops.
2. **Mutual friend count off by one** — The mutual friends calculation includes
   the queried users themselves, inflating the count by 1.
3. **Remove friendship only one direction** — `remove_friendship` only removes B
   from A's friends list, but not A from B's. The graph becomes inconsistent.

## Features to Implement

1. **Friend Suggestions** — Suggest friends based on number of mutual connections.
   Return users sorted by mutual friend count (descending). Exclude existing friends
   and the user themselves.
2. **Degree of Separation (BFS)** — Find the shortest path length between two users.
   Return -1 if no path exists.
3. **Blocking** — When user A blocks user B, they cannot be friends, B cannot appear
   in A's suggestions, and A cannot appear in B's suggestions.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
