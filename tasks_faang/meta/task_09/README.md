# Task 09: Feature Flags Service

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Feature Flags Service. It manages feature rollouts with
percentage-based targeting, user segment rules, and flag dependencies. Feature
flags control which users see new features.

## Existing Codebase

The `app.py` file contains a `FeatureFlagService` that:
- Defines flags with percentage rollout, targeting rules, and dependencies
- Evaluates whether a flag is enabled for a given user
- Supports AND/OR logic for targeting rules
- Manages flag dependencies (flag A requires flag B to be enabled)

## Known Bugs (3-4 to find and fix)

1. **Percentage rollout not deterministic** — The hash function for determining
   whether a user falls in the rollout percentage uses `random()` instead of a
   deterministic hash. Same user gets different results on each call.
2. **Targeting rules AND/OR logic is wrong** — AND conditions are evaluated as
   OR, and vice versa. Rules that should all match (AND) pass if any match.
3. **Flag dependency evaluation broken** — When flag A depends on flag B, the
   dependency check doesn't actually evaluate flag B for the user. It only checks
   if flag B exists, not if it's enabled for that user.

## Features to Implement

1. **Gradual Rollout Scheduling** — Schedule a flag to gradually increase its
   rollout percentage over time (e.g., 10% on day 1, 50% on day 3, 100% on day 7).
2. **Flag Audit Log** — Record all flag state changes (created, updated, toggled)
   with timestamps and who made the change.
3. **Kill Switch** — Immediately disable a flag for all users, overriding all
   rules and percentages.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
