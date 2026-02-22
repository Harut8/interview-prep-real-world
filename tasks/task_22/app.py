import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MessageStatus(Enum):
    RECEIVED = "received"
    BUFFERED = "buffered"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Message:
    id: str
    sender: str
    content: str
    timestamp: float
    sequence_num: int
    channel: str = "default"
    depends_on: list[str] = field(default_factory=list)
    status: MessageStatus = MessageStatus.RECEIVED


class MessageOrderingService:
    """Service for ordering and delivering real-time messages."""

    def __init__(self):
        self.messages: dict[str, Message] = {}
        self.channels: dict[str, list[Message]] = {}
        self._next_expected_seq: dict[str, int] = {}
        self._delivered: list[str] = []

    def add_message(self, message: Message) -> bool:
        """Add a message to the ordering buffer.

        Returns True if message was added, False if rejected.
        """
        # BUG: no duplicate detection — same message ID can overwrite
        self.messages[message.id] = message

        channel = message.channel
        if channel not in self.channels:
            self.channels[channel] = []
            self._next_expected_seq[channel] = 0

        self.channels[channel].append(message)
        message.status = MessageStatus.BUFFERED
        return True

    def get_ordered_messages(self, channel: str = "default") -> list[Message]:
        """Get messages in correct order for a channel."""
        if channel not in self.channels:
            return []

        # BUG: sorts on every call — should maintain a sorted structure
        messages = self.channels[channel]
        messages.sort(key=lambda m: (m.sequence_num, m.timestamp))
        return list(messages)

    def deliver_next(self, channel: str = "default") -> Optional[Message]:
        """Deliver the next message in sequence for a channel."""
        if channel not in self.channels:
            return None

        expected_seq = self._next_expected_seq.get(channel, 0)
        ordered = self.get_ordered_messages(channel)

        for msg in ordered:
            if msg.status == MessageStatus.BUFFERED:
                # BUG: delivers whatever is next, even if there's a gap
                # Should only deliver if msg.sequence_num == expected_seq
                msg.status = MessageStatus.DELIVERED
                self._delivered.append(msg.id)
                self._next_expected_seq[channel] = msg.sequence_num + 1
                return msg

        return None

    def is_duplicate(self, message_id: str) -> bool:
        """Check if a message ID has already been seen."""
        # BUG: this exists but add_message never calls it
        return message_id in self.messages

    def compare_timestamps(self, t1: float, t2: float) -> int:
        """Compare two timestamps. Returns -1, 0, or 1."""
        # BUG: uses exact float comparison
        if t1 == t2:
            return 0
        return -1 if t1 < t2 else 1

    def get_pending_count(self, channel: str = "default") -> int:
        """Get count of messages waiting to be delivered."""
        if channel not in self.channels:
            return 0
        return sum(1 for m in self.channels[channel] if m.status == MessageStatus.BUFFERED)


# TODO: Add MessageBuffer with configurable timeout for reordering
# TODO: Add acknowledge(message_id) method
# TODO: Add get_unacknowledged() method
# TODO: Add causal ordering (depends_on support)
# TODO: Add get_delivery_stats() method
