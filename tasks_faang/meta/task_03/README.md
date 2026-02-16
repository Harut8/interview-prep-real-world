# Task 03: Content Moderation Pipeline

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Content Moderation Pipeline. The system classifies user
content against a set of moderation rules, applies actions (warn, hide, remove),
and maintains an immutable audit history.

## Existing Codebase

The `app.py` file contains a `ModerationPipeline` that:
- Defines moderation rules with priorities, regex patterns, and actions
- Evaluates content against all rules
- Records moderation decisions in a history log
- Supports different severity levels

## Known Bugs (3-4 to find and fix)

1. **Rule priority not respected** — All matching rules are applied equally instead
   of highest-priority rule taking precedence. Only the highest-priority matching
   rule's action should be applied.
2. **Catastrophic regex backtracking** — Some regex patterns have catastrophic
   backtracking that hangs on certain inputs (e.g., nested quantifiers).
3. **Moderation history is mutable** — The history records can be modified after
   creation, breaking the audit trail. History entries should be frozen/immutable.

## Features to Implement

1. **Appeal System** — Users can appeal moderation decisions. Appeals are reviewed
   and can be approved (reverses action) or denied.
2. **Bulk Moderation** — Apply moderation action to multiple content items at once.
3. **Confidence-based Auto-moderation** — When a rule match has high confidence
   (> 0.9), auto-apply the action. Medium confidence (0.5-0.9) queues for human
   review. Low confidence (< 0.5) takes no action.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
