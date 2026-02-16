"""Tests for Messaging Service."""

import time
import pytest
from app import MessagingService, MessageStatus


@pytest.fixture
def service() -> MessagingService:
    svc = MessagingService()
    return svc


@pytest.fixture
def thread_with_messages(service: MessagingService):
    thread = service.create_thread(["alice", "bob"])
    # Send messages out of timestamp order
    m1 = service.send_message(thread.thread_id, "alice", "Hello!", timestamp=1000.0)
    m2 = service.send_message(thread.thread_id, "bob", "Hey!", timestamp=900.0)  # Earlier
    m3 = service.send_message(thread.thread_id, "alice", "How are you?", timestamp=1100.0)
    return thread, [m1, m2, m3]


class TestMessageOrdering:
    def test_messages_ordered_by_timestamp(self, service, thread_with_messages):
        """FAILING: Messages should be returned sorted by timestamp.

        Bug: Messages are returned in insertion order, not by timestamp.
        """
        thread, msgs = thread_with_messages
        result = service.get_thread_messages(thread.thread_id)
        timestamps = [m.timestamp for m in result]
        assert timestamps == sorted(timestamps), (
            f"Messages should be sorted by timestamp. Got: {timestamps}"
        )

    def test_earliest_message_first(self, service, thread_with_messages):
        """FAILING: First message in thread view should be the earliest."""
        thread, msgs = thread_with_messages
        result = service.get_thread_messages(thread.thread_id)
        assert result[0].timestamp == 900.0, "Earliest message (900.0) should be first"


class TestReadReceipts:
    def test_mark_as_read_correct_thread(self, service):
        """FAILING: mark_as_read should update the specified thread, not another.

        Bug: Wrong thread is used for the read update.
        """
        t1 = service.create_thread(["alice", "bob"])
        t2 = service.create_thread(["alice", "carol"])

        service.send_message(t1.thread_id, "bob", "msg in t1", timestamp=100.0)
        service.send_message(t2.thread_id, "carol", "msg in t2", timestamp=100.0)

        # Mark t2 as read for alice
        count = service.mark_as_read("alice", t2.thread_id, up_to_timestamp=200.0)
        assert count == 1, f"Should mark 1 message as read in t2, got {count}"

        # Verify t2 messages are read
        t2_msgs = service.get_thread_messages(t2.thread_id)
        for msg in t2_msgs:
            if msg.sender_id != "alice":
                assert msg.status == MessageStatus.READ

    def test_unread_count_decreases(self, service):
        """FAILING: Unread count should decrease when messages are read.

        Bug: Unread count is not decremented after mark_as_read.
        """
        thread = service.create_thread(["alice", "bob"])
        service.send_message(thread.thread_id, "bob", "msg1", timestamp=100.0)
        service.send_message(thread.thread_id, "bob", "msg2", timestamp=200.0)

        assert service.get_unread_count("alice", thread.thread_id) == 2

        service.mark_as_read("alice", thread.thread_id, up_to_timestamp=200.0)
        count = service.get_unread_count("alice", thread.thread_id)
        assert count == 0, f"Unread count should be 0 after reading all, got {count}"


class TestSendMessage:
    def test_send_increments_unread(self, service):
        """PASSING: Sending a message should increment unread count for others."""
        thread = service.create_thread(["alice", "bob"])
        service.send_message(thread.thread_id, "alice", "hi")
        assert service.get_unread_count("bob", thread.thread_id) == 1
        assert service.get_unread_count("alice", thread.thread_id) == 0

    def test_send_to_nonexistent_thread(self, service):
        """PASSING: Sending to nonexistent thread should raise."""
        with pytest.raises(ValueError):
            service.send_message("fake_thread", "alice", "hi")


class TestReactions:
    def test_add_reaction(self, service):
        """TODO: Add emoji reaction to a message."""
        thread = service.create_thread(["alice", "bob"])
        msg = service.send_message(thread.thread_id, "alice", "Great news!")
        result = service.add_reaction(msg.message_id, thread.thread_id, "bob", "👍")
        assert result is True
        # Verify reaction is stored
        messages = service.get_thread_messages(thread.thread_id)
        assert messages[0].reactions.get("bob") == "👍"

    def test_change_reaction(self, service):
        """TODO: Changing reaction should replace the old one."""
        thread = service.create_thread(["alice", "bob"])
        msg = service.send_message(thread.thread_id, "alice", "News")
        service.add_reaction(msg.message_id, thread.thread_id, "bob", "👍")
        service.add_reaction(msg.message_id, thread.thread_id, "bob", "❤️")
        messages = service.get_thread_messages(thread.thread_id)
        assert messages[0].reactions.get("bob") == "❤️"
        assert len(messages[0].reactions) == 1

    def test_remove_reaction(self, service):
        """TODO: Removing reaction should clear it."""
        thread = service.create_thread(["alice", "bob"])
        msg = service.send_message(thread.thread_id, "alice", "News")
        service.add_reaction(msg.message_id, thread.thread_id, "bob", "👍")
        service.remove_reaction(msg.message_id, thread.thread_id, "bob")
        messages = service.get_thread_messages(thread.thread_id)
        assert "bob" not in messages[0].reactions


class TestTypingIndicators:
    def test_typing_indicator(self, service):
        """TODO: Typing indicators should track who is typing."""
        thread = service.create_thread(["alice", "bob"])
        now = time.time()
        service.set_typing(thread.thread_id, "alice")
        typing = service.get_typing_users(thread.thread_id, now=now)
        assert "alice" in typing

    def test_typing_expires(self, service):
        """TODO: Typing indicator should expire after timeout."""
        thread = service.create_thread(["alice", "bob"])
        service.set_typing(thread.thread_id, "alice")
        # Check after timeout
        future = time.time() + 10  # well past the 5-second timeout
        typing = service.get_typing_users(thread.thread_id, now=future)
        assert "alice" not in typing


class TestMessageDeletion:
    def test_soft_delete_own_message(self, service):
        """TODO: Users can soft-delete their own messages."""
        thread = service.create_thread(["alice", "bob"])
        msg = service.send_message(thread.thread_id, "alice", "Oops wrong chat")
        result = service.delete_message(msg.message_id, thread.thread_id, "alice")
        assert result is True
        messages = service.get_thread_messages(thread.thread_id)
        assert messages[0].is_deleted is True
        assert messages[0].content == "This message was deleted"

    def test_cannot_delete_others_message(self, service):
        """TODO: Cannot delete another user's message."""
        thread = service.create_thread(["alice", "bob"])
        msg = service.send_message(thread.thread_id, "alice", "My message")
        result = service.delete_message(msg.message_id, thread.thread_id, "bob")
        assert result is False
