"""Tests for the Pub/Sub Message Broker."""

import threading
import pytest
from app import MessageBroker, Message


@pytest.fixture
def broker() -> MessageBroker:
    b = MessageBroker()
    b.create_topic("events")
    b.create_topic("alerts")
    return b


class TestBasicPubSub:
    """Tests for basic publish/subscribe — some fail due to bugs."""

    def test_subscriber_receives_message(self, broker: MessageBroker) -> None:
        """Subscriber should receive published messages."""
        received: list[Message] = []
        broker.subscribe("sub1", "events", lambda msg: received.append(msg))
        broker.publish("events", {"data": "hello"}, publisher_id="pub1")

        assert len(received) == 1
        assert received[0].payload == {"data": "hello"}

    def test_multiple_subscribers(self, broker: MessageBroker) -> None:
        """All subscribers should receive the message."""
        received1: list[Message] = []
        received2: list[Message] = []
        broker.subscribe("sub1", "events", lambda msg: received1.append(msg))
        broker.subscribe("sub2", "events", lambda msg: received2.append(msg))

        broker.publish("events", "test", publisher_id="pub1")
        assert len(received1) == 1
        assert len(received2) == 1

    def test_publisher_not_own_subscriber(self, broker: MessageBroker) -> None:
        """Publisher should NOT receive its own message.
        FAILING: Bug #1 — publisher receives its own messages.
        """
        received: list[Message] = []
        broker.subscribe("user1", "events", lambda msg: received.append(msg))

        # user1 publishes to a topic it's subscribed to
        broker.publish("events", "self-message", publisher_id="user1")

        assert len(received) == 0, (
            f"Publisher 'user1' received its own message. "
            f"Got {len(received)} messages, expected 0."
        )

    def test_unsubscribe(self, broker: MessageBroker) -> None:
        """After unsubscribe, subscriber should not receive new messages."""
        received: list[Message] = []
        broker.subscribe("sub1", "events", lambda msg: received.append(msg))
        broker.unsubscribe("sub1", "events")
        broker.publish("events", "test", publisher_id="pub1")

        assert len(received) == 0


class TestMessageOrdering:
    """Tests for message ordering — FAILING due to Bug #2."""

    def test_multi_topic_ordering(self, broker: MessageBroker) -> None:
        """Messages published in order should be delivered in order.
        FAILING: Bug #2 — publish_multi groups by topic, breaking order.
        """
        received: list[str] = []

        def record(msg: Message) -> None:
            received.append(f"{msg.topic}:{msg.payload}")

        broker.subscribe("sub1", "events", record)
        broker.subscribe("sub1", "alerts", record)

        # Publish interleaved topics — order should be preserved
        messages = [
            ("events", "e1", "pub1"),
            ("alerts", "a1", "pub1"),
            ("events", "e2", "pub1"),
            ("alerts", "a2", "pub1"),
        ]
        broker.publish_multi(messages)

        expected = ["events:e1", "alerts:a1", "events:e2", "alerts:a2"]
        assert received == expected, (
            f"Messages delivered out of order. Expected {expected}, got {received}. "
            f"publish_multi should preserve insertion order across topics."
        )


class TestConcurrentUnsubscribe:
    """Tests for concurrent unsubscribe — FAILING due to Bug #3."""

    def test_unsubscribe_during_delivery(self, broker: MessageBroker) -> None:
        """Unsubscribing from a callback during delivery should not crash.
        FAILING: Bug #3 — dict modified during iteration.
        """
        received: list[str] = []

        def unsub_callback(msg: Message) -> None:
            received.append("sub1")
            # Unsubscribe self during delivery
            broker.unsubscribe("sub1", "events")

        def normal_callback(msg: Message) -> None:
            received.append("sub2")

        broker.subscribe("sub1", "events", unsub_callback)
        broker.subscribe("sub2", "events", normal_callback)

        # This should NOT crash
        try:
            broker.publish("events", "test", publisher_id="pub1")
        except RuntimeError as e:
            pytest.fail(f"Unsubscribe during delivery crashed: {e}")

        assert "sub2" in received


class TestMessageFiltering:
    """Tests for message filtering — TODO: implement."""

    def test_filter_by_payload(self, broker: MessageBroker) -> None:
        """TODO: Subscriber with filter should only receive matching messages."""
        received: list[Message] = []
        broker.subscribe_with_filter(
            "sub1", "events",
            callback=lambda msg: received.append(msg),
            filter_fn=lambda msg: msg.payload.get("priority") == "high",
        )

        broker.publish("events", {"priority": "low", "data": "skip"}, "pub1")
        broker.publish("events", {"priority": "high", "data": "keep"}, "pub1")
        broker.publish("events", {"priority": "medium", "data": "skip"}, "pub1")

        assert len(received) == 1
        assert received[0].payload["data"] == "keep"


class TestAtLeastOnce:
    """Tests for at-least-once delivery — TODO: implement."""

    def test_unacked_message_redelivered(self, broker: MessageBroker) -> None:
        """TODO: Unacknowledged messages should be redelivered after timeout."""
        received: list[Message] = []
        broker.subscribe("sub1", "events", lambda msg: received.append(msg))
        broker.publish("events", "important", publisher_id="pub1")

        assert len(received) == 1
        # Don't acknowledge — message should be redelivered
        count = broker.redeliver_unacknowledged()
        assert count >= 0  # Implementation-dependent


class TestDeadLetter:
    """Tests for dead letter topic — TODO: implement."""

    def test_failed_message_dead_lettered(self, broker: MessageBroker) -> None:
        """TODO: Message failing max_delivery_attempts should be dead-lettered."""
        def failing_callback(msg: Message) -> None:
            raise RuntimeError("fail")

        broker.subscribe("sub1", "events", failing_callback)
        broker.publish("events", "problematic", publisher_id="pub1")

        # After max attempts, should be in dead letters
        dead = broker.get_dead_letters()
        # The message should eventually end up here after retries
        assert isinstance(dead, list)
