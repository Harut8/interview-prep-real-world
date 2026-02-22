import pytest
from app import Channel, NotificationService, Priority


@pytest.fixture
def service():
    return NotificationService()


def test_create_notification(service):
    notif_id = service.create_notification(
        recipient="user@example.com",
        subject="Hello",
        template="Hello {name}!",
        context={"name": "Alice"},
        channels=[Channel.EMAIL],
    )
    assert notif_id in service.notifications


def test_render_template(service):
    result = service.render_template("Hello {name}!", {"name": "Alice"})
    assert result == "Hello Alice!"


# FAILS — fix template to handle missing keys gracefully
def test_render_template_missing_key(service):
    result = service.render_template(
        "Hello {name}, your order {order_id} is ready!",
        {"name": "Alice"},  # missing order_id
    )
    assert "Alice" in result
    # Should not crash, should use a default value or placeholder


# FAILS — fix priority ordering (HIGH should come first)
def test_priority_ordering(service):
    service.create_notification("a", "Low", "", {}, [Channel.PUSH], Priority.LOW)
    service.create_notification("b", "High", "", {}, [Channel.PUSH], Priority.HIGH)
    service.create_notification("c", "Medium", "", {}, [Channel.PUSH], Priority.MEDIUM)

    pending = service.get_pending_by_priority()
    priorities = [n.priority for n in pending]
    assert priorities == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


# FAILS — fix duplicate sending
def test_send_stops_after_success(service):
    send_counts = {"email": 0, "push": 0}

    class CountingEmailSender:
        def send(self, *args):
            send_counts["email"] += 1
            return True

    class CountingPushSender:
        def send(self, *args):
            send_counts["push"] += 1
            return True

    service.senders[Channel.EMAIL] = CountingEmailSender()
    service.senders[Channel.PUSH] = CountingPushSender()

    notif_id = service.create_notification(
        "user@test.com",
        "Test",
        "Hello",
        {},
        [Channel.EMAIL, Channel.PUSH],
    )
    service.send(notif_id)
    # Should stop after email succeeds — push should NOT be called
    assert send_counts["email"] == 1
    assert send_counts["push"] == 0


# TODO: Add tests for NotificationQueue
# TODO: Add tests for delivery report
# TODO: Add tests for retry mechanism
