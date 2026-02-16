# Task 04: Messaging Service

**Company Style:** Meta | **Time Limit:** 60 minutes | **Level:** Mid/Senior

## Overview

You are building Meta's Messaging Service (like Messenger). It handles sending
messages between users, organizing them into threads, tracking read receipts,
and maintaining unread counts.

## Existing Codebase

The `app.py` file contains a `MessagingService` that:
- Creates threads between users
- Sends messages to threads
- Retrieves messages in thread order
- Tracks read receipts and unread counts

## Known Bugs (3-4 to find and fix)

1. **Messages not ordered by timestamp** — `get_thread_messages` returns messages
   in insertion order, not sorted by timestamp. When messages arrive out of order,
   the display is wrong.
2. **Read receipts update wrong thread** — `mark_as_read` uses the wrong thread ID
   lookup, updating read status on the incorrect thread.
3. **Unread count doesn't decrease** — When messages are marked as read, the unread
   count for the user is not decremented.

## Features to Implement

1. **Message Reactions** — Users can add emoji reactions to messages (one reaction
   per user per message, can change).
2. **Typing Indicators** — Track which users are currently typing in a thread.
   Typing status expires after 5 seconds.
3. **Message Deletion (soft delete)** — Users can delete their own messages.
   Deleted messages should show as "This message was deleted" instead of content.

## Tests

- `tests/test_app.py` contains tests. Some pass, some fail due to bugs, some are TODOs.

## Rules

- Fix all bugs so failing tests pass
- Implement features so TODO tests pass
- Do NOT modify test files
- Python 3.10+, use only stdlib + packages in requirements.txt
