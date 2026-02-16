"""
Pub/Sub Message Broker

In-memory publish/subscribe system with topics, message ordering, and delivery
guarantees.
"""

from __future__ import annotations

import time
import uuid
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


@dataclass
class Message:
    """A pub/sub message."""
    message_id: str
    topic: str
    payload: Any
    publisher_id: str
    timestamp: float = field(default_factory=time.time)
    headers: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def create(topic: str, payload: Any, publisher_id: str, **headers: str) -> "Message":
        return Message(
            message_id=str(uuid.uuid4()),
            topic=topic,
            payload=payload,
            publisher_id=publisher_id,
            headers=headers,
        )


@dataclass
class Subscription:
    """A subscriber's subscription to a topic."""
    subscriber_id: str
    topic: str
    callback: Callable[[Message], None]
    filter_fn: Optional[Callable[[Message], bool]] = None


@dataclass
class DeliveryRecord:
    """Tracks delivery of a message to a subscriber."""
    message_id: str
    subscriber_id: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    last_attempt: Optional[float] = None


class MessageBroker:
    """In-memory pub/sub message broker."""

    def __init__(self, max_delivery_attempts: int = 3, ack_timeout: float = 30.0) -> None:
        self.max_delivery_attempts = max_delivery_attempts
        self.ack_timeout = ack_timeout

        # topic -> set of Subscriptions
        self.subscriptions: dict[str, dict[str, Subscription]] = defaultdict(dict)
        # All messages in publish order
        self.messages: list[Message] = []
        # message_id -> {subscriber_id -> DeliveryRecord}
        self.delivery_records: dict[str, dict[str, DeliveryRecord]] = {}
        # Dead letter messages
        self.dead_letters: list[Message] = []
        self._lock = threading.Lock()
        # Global order counter for multi-topic ordering
        self._order_counter: int = 0

    def create_topic(self, topic: str) -> None:
        """Create a new topic (no-op if already exists)."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = {}

    def subscribe(
        self,
        subscriber_id: str,
        topic: str,
        callback: Callable[[Message], None],
        filter_fn: Optional[Callable[[Message], bool]] = None,
    ) -> None:
        """Subscribe to a topic with a callback for message delivery."""
        self.create_topic(topic)
        sub = Subscription(
            subscriber_id=subscriber_id,
            topic=topic,
            callback=callback,
            filter_fn=filter_fn,
        )
        self.subscriptions[topic][subscriber_id] = sub

    def unsubscribe(self, subscriber_id: str, topic: str) -> None:
        """Unsubscribe from a topic."""
        # BUG #3: Modifying the subscriptions dict directly during iteration
        # in publish() can cause RuntimeError. This is fine on its own, but
        # if called from within a callback during delivery, it crashes.
        if topic in self.subscriptions:
            self.subscriptions[topic].pop(subscriber_id, None)

    def publish(self, topic: str, payload: Any, publisher_id: str) -> Optional[Message]:
        """Publish a message to a topic."""
        if topic not in self.subscriptions:
            return None

        msg = Message.create(topic, payload, publisher_id)
        self._order_counter += 1
        self.messages.append(msg)

        # Deliver to all subscribers
        # BUG #3: Iterating over dict directly — if a callback calls unsubscribe,
        # this will raise RuntimeError: dictionary changed size during iteration.
        for sub_id, sub in self.subscriptions[topic].items():
            # BUG #1: Doesn't exclude the publisher from delivery.
            # If publisher_id == sub.subscriber_id, the publisher receives its own message.
            try:
                sub.callback(msg)
            except Exception:
                pass  # Swallow delivery errors

        return msg

    def publish_multi(
        self,
        messages: list[tuple[str, Any, str]],
    ) -> list[Message]:
        """Publish multiple messages to potentially different topics.
        Returns messages in publish order.
        """
        published: list[Message] = []
        # BUG #2: Messages are published and delivered topic-by-topic, not in
        # the order they appear in the input list. A subscriber to multiple topics
        # may receive messages out of order.
        by_topic: dict[str, list[tuple[Any, str]]] = defaultdict(list)
        for topic, payload, publisher_id in messages:
            by_topic[topic].append((payload, publisher_id))

        for topic, items in by_topic.items():
            for payload, publisher_id in items:
                msg = self.publish(topic, payload, publisher_id)
                if msg:
                    published.append(msg)

        return published

    # -------------------------------------------------------------------------
    # TODO: Implement message filtering
    # -------------------------------------------------------------------------
    def subscribe_with_filter(
        self,
        subscriber_id: str,
        topic: str,
        callback: Callable[[Message], None],
        filter_fn: Callable[[Message], bool],
    ) -> None:
        """Subscribe with a filter — only messages passing the filter are delivered."""
        raise NotImplementedError("Message filtering not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement at-least-once delivery
    # -------------------------------------------------------------------------
    def acknowledge(self, message_id: str, subscriber_id: str) -> None:
        """Acknowledge receipt of a message."""
        raise NotImplementedError("Acknowledgment not implemented")

    def redeliver_unacknowledged(self) -> int:
        """Redeliver messages that haven't been acknowledged within ack_timeout.
        Returns the number of messages redelivered.
        """
        raise NotImplementedError("Redelivery not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement dead letter topic
    # -------------------------------------------------------------------------
    def move_to_dead_letter(self, message_id: str, subscriber_id: str) -> None:
        """Move a message to the dead letter topic after max delivery attempts."""
        raise NotImplementedError("Dead letter not implemented")

    def get_dead_letters(self) -> list[Message]:
        """Return all dead-lettered messages."""
        raise NotImplementedError("Dead letter retrieval not implemented")
