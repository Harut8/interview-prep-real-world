"""
Messaging Service
Real-time-like message delivery with threads, read receipts, and unread counts.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MessageStatus(Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


@dataclass
class Message:
    message_id: str
    thread_id: str
    sender_id: str
    content: str
    timestamp: float
    status: MessageStatus = MessageStatus.SENT
    is_deleted: bool = False
    reactions: dict[str, str] = field(default_factory=dict)  # user_id -> emoji


@dataclass
class Thread:
    thread_id: str
    participant_ids: list[str]
    created_at: float = field(default_factory=time.time)
    messages: list[Message] = field(default_factory=list)


@dataclass
class TypingIndicator:
    user_id: str
    thread_id: str
    started_at: float


class MessagingService:
    """Messaging service with threads, read receipts, and more."""

    TYPING_TIMEOUT = 5.0  # seconds before typing indicator expires

    def __init__(self) -> None:
        self.threads: dict[str, Thread] = {}
        self.user_threads: dict[str, list[str]] = {}  # user_id -> thread_ids
        # Read watermark: the timestamp up to which user has read messages
        self.read_watermarks: dict[str, dict[str, float]] = {}  # user_id -> {thread_id -> timestamp}
        self.unread_counts: dict[str, dict[str, int]] = {}  # user_id -> {thread_id -> count}
        self.typing_indicators: dict[str, dict[str, TypingIndicator]] = {}  # thread_id -> {user_id -> indicator}

    def create_thread(self, participant_ids: list[str]) -> Thread:
        """Create a new message thread between participants."""
        thread_id = str(uuid.uuid4())
        thread = Thread(thread_id=thread_id, participant_ids=participant_ids)
        self.threads[thread_id] = thread
        for uid in participant_ids:
            if uid not in self.user_threads:
                self.user_threads[uid] = []
            self.user_threads[uid].append(thread_id)
            if uid not in self.unread_counts:
                self.unread_counts[uid] = {}
            self.unread_counts[uid][thread_id] = 0
            if uid not in self.read_watermarks:
                self.read_watermarks[uid] = {}
            self.read_watermarks[uid][thread_id] = 0.0
        return thread

    def send_message(self, thread_id: str, sender_id: str, content: str,
                     timestamp: float | None = None) -> Message:
        """Send a message to a thread."""
        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")
        thread = self.threads[thread_id]
        if sender_id not in thread.participant_ids:
            raise ValueError(f"User {sender_id} is not a participant")

        msg = Message(
            message_id=str(uuid.uuid4()),
            thread_id=thread_id,
            sender_id=sender_id,
            content=content,
            timestamp=timestamp or time.time(),
        )
        thread.messages.append(msg)

        # Increment unread count for other participants
        for uid in thread.participant_ids:
            if uid != sender_id:
                self.unread_counts[uid][thread_id] = (
                    self.unread_counts.get(uid, {}).get(thread_id, 0) + 1
                )
        return msg

    def get_thread_messages(self, thread_id: str) -> list[Message]:
        """Get all messages in a thread, ordered by timestamp.

        BUG: Returns messages in insertion order, not sorted by timestamp.
        """
        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")
        # BUG: No sorting — just returns in list order
        return list(self.threads[thread_id].messages)

    def mark_as_read(self, user_id: str, thread_id: str, up_to_timestamp: float) -> int:
        """Mark messages as read up to a given timestamp.

        Returns the number of messages marked as read.

        BUG 1: Uses wrong thread lookup for updating read status.
        BUG 2: Does not decrement unread count.
        """
        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")

        # BUG: Iterates over the FIRST thread in self.threads instead of the specified one
        wrong_thread = next(iter(self.threads.values()))
        messages = wrong_thread.messages

        read_count = 0
        for msg in messages:
            if (msg.sender_id != user_id
                    and msg.status != MessageStatus.READ
                    and msg.timestamp <= up_to_timestamp):
                msg.status = MessageStatus.READ
                read_count += 1

        # Update watermark
        if user_id in self.read_watermarks:
            current = self.read_watermarks[user_id].get(thread_id, 0.0)
            self.read_watermarks[user_id][thread_id] = max(current, up_to_timestamp)

        # BUG: Does not update unread_counts — count stays the same
        return read_count

    def get_unread_count(self, user_id: str, thread_id: str) -> int:
        """Get unread message count for a user in a thread."""
        return self.unread_counts.get(user_id, {}).get(thread_id, 0)

    def add_reaction(self, message_id: str, thread_id: str, user_id: str,
                     emoji: str) -> bool:
        """Add or update a reaction on a message.

        TODO: Implement reactions. One reaction per user per message.
        """
        return False

    def remove_reaction(self, message_id: str, thread_id: str,
                        user_id: str) -> bool:
        """Remove a user's reaction from a message.

        TODO: Implement reaction removal.
        """
        return False

    def set_typing(self, thread_id: str, user_id: str) -> None:
        """Set typing indicator for a user in a thread.

        TODO: Implement typing indicators.
        """
        pass

    def get_typing_users(self, thread_id: str, now: float | None = None) -> list[str]:
        """Get list of users currently typing in a thread.

        Indicators expire after TYPING_TIMEOUT seconds.

        TODO: Implement typing indicator query.
        """
        return []

    def delete_message(self, message_id: str, thread_id: str,
                       user_id: str) -> bool:
        """Soft-delete a message. Only the sender can delete.

        Deleted messages should have content replaced with
        'This message was deleted'.

        TODO: Implement soft delete.
        """
        return False
