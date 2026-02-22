import pytest
import time
from app import MessageOrderingService, Message, MessageStatus


@pytest.fixture
def service():
    return MessageOrderingService()


def make_message(id: str, seq: int, content: str = "test", channel: str = "default",
                 depends_on: list[str] = None) -> Message:
    return Message(
        id=id,
        sender="user1",
        content=content,
        timestamp=time.time(),
        sequence_num=seq,
        channel=channel,
        depends_on=depends_on or [],
    )


def test_add_message(service):
    msg = make_message("m1", 0)
    assert service.add_message(msg) is True
    assert "m1" in service.messages


# FAILS — fix duplicate detection
def test_add_duplicate_rejected(service):
    msg1 = make_message("m1", 0, content="first")
    msg2 = make_message("m1", 0, content="duplicate")
    assert service.add_message(msg1) is True
    assert service.add_message(msg2) is False
    assert service.messages["m1"].content == "first"


def test_ordered_messages(service):
    service.add_message(make_message("m3", 2))
    service.add_message(make_message("m1", 0))
    service.add_message(make_message("m2", 1))

    ordered = service.get_ordered_messages()
    seqs = [m.sequence_num for m in ordered]
    assert seqs == [0, 1, 2]


# FAILS — fix gap handling: should not deliver seq 2 if seq 1 is missing
def test_deliver_respects_sequence_gaps(service):
    service.add_message(make_message("m1", 0))
    service.add_message(make_message("m3", 2))  # gap: seq 1 is missing

    msg = service.deliver_next()
    assert msg.id == "m1"

    msg = service.deliver_next()
    # Should return None because seq 1 is missing
    assert msg is None


# FAILS — fix float timestamp comparison
def test_timestamp_comparison_precision(service):
    t1 = 0.1 + 0.2  # 0.30000000000000004
    t2 = 0.3
    assert service.compare_timestamps(t1, t2) == 0


def test_deliver_in_order(service):
    service.add_message(make_message("m1", 0))
    service.add_message(make_message("m2", 1))

    msg1 = service.deliver_next()
    assert msg1.id == "m1"
    assert msg1.status == MessageStatus.DELIVERED

    msg2 = service.deliver_next()
    assert msg2.id == "m2"


def test_pending_count(service):
    service.add_message(make_message("m1", 0))
    service.add_message(make_message("m2", 1))
    assert service.get_pending_count() == 2

    service.deliver_next()
    assert service.get_pending_count() == 1


# TODO: Add tests for MessageBuffer with timeout
# TODO: Add tests for acknowledge and get_unacknowledged
# TODO: Add tests for causal ordering (depends_on)
# TODO: Add tests for get_delivery_stats
