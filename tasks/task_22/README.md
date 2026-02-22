# Task 22: Real-Time Message Ordering — Fix Bugs & Add Delivery Guarantees

**Time limit: 60 minutes**

## Existing Codebase

A real-time message ordering system that receives messages with timestamps and sequence numbers, reorders them, and delivers them in the correct order. Handles out-of-order delivery and duplicate detection.

## Problems to Fix

1. The `add_message` method doesn't detect duplicate messages — same message can be processed twice.
2. The `get_ordered_messages` method uses a naive sort on every call instead of maintaining a sorted structure.
3. The `deliver` method doesn't handle gaps in sequence numbers — it skips messages instead of waiting.
4. Timestamp comparison uses `==` for floats which can fail due to precision issues.

## Features to Implement

1. Add a `MessageBuffer` with configurable timeout — holds messages for reordering before delivery.
2. Add `acknowledge(message_id)` — marks a message as successfully processed.
3. Add `get_unacknowledged()` — returns messages delivered but not yet acknowledged (for retry).
4. Add causal ordering support: messages can declare `depends_on` (a list of message IDs that must be delivered first).
5. Add `get_delivery_stats()` — returns metrics: total received, delivered, pending, duplicates dropped, avg reorder delay.
6. Write tests for all fixed bugs and new features.

## What We Evaluate

- Ordering algorithms and data structures
- Duplicate detection
- Gap handling and buffering
- Causal ordering logic
- Test coverage and edge cases
