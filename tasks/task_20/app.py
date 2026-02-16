import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Channel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class DeliveryStatus(Enum):
    PENDING = "pending"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass
class Notification:
    id: str
    recipient: str
    subject: str
    template: str
    context: dict[str, Any]
    channels: list[Channel]
    priority: Priority = Priority.MEDIUM
    status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: float = field(default_factory=time.time)


class EmailSender:
    """Simulated email sender."""
    def send(self, recipient: str, subject: str, body: str) -> bool:
        # Simulate: 90% success rate
        return hash(recipient + subject) % 10 != 0

    def __str__(self):
        return "EmailSender"


class SMSSender:
    """Simulated SMS sender."""
    def send(self, recipient: str, body: str) -> bool:
        return hash(recipient) % 10 != 0

    def __str__(self):
        return "SMSSender"


class PushSender:
    """Simulated push notification sender."""
    def send(self, recipient: str, title: str, body: str) -> bool:
        return True  # push always succeeds in simulation

    def __str__(self):
        return "PushSender"


class NotificationService:
    """Service for sending notifications through multiple channels."""

    def __init__(self):
        self.senders = {
            Channel.EMAIL: EmailSender(),
            Channel.SMS: SMSSender(),
            Channel.PUSH: PushSender(),
        }
        self.notifications: dict[str, Notification] = {}

    def create_notification(
        self,
        recipient: str,
        subject: str,
        template: str,
        context: dict[str, Any],
        channels: list[Channel],
        priority: Priority = Priority.MEDIUM,
    ) -> str:
        """Create a new notification."""
        notif_id = str(uuid.uuid4())[:8]
        notification = Notification(
            id=notif_id,
            recipient=recipient,
            subject=subject,
            template=template,
            context=context,
            channels=channels,
            priority=priority,
        )
        self.notifications[notif_id] = notification
        return notif_id

    def render_template(self, template: str, context: dict[str, Any]) -> str:
        """Render a notification template with context."""
        # BUG: crashes on missing keys instead of using defaults
        return template.format(**context)

    def send(self, notification_id: str) -> bool:
        """Send a notification through configured channels."""
        notification = self.notifications.get(notification_id)
        if not notification:
            raise ValueError(f"Notification {notification_id} not found")

        body = self.render_template(notification.template, notification.context)
        notification.status = DeliveryStatus.SENDING

        success = False
        for channel in notification.channels:
            sender = self.senders.get(channel)
            if not sender:
                continue

            try:
                if channel == Channel.EMAIL:
                    result = sender.send(notification.recipient, notification.subject, body)
                elif channel == Channel.SMS:
                    result = sender.send(notification.recipient, body)
                elif channel == Channel.PUSH:
                    result = sender.send(notification.recipient, notification.subject, body)

                if result:
                    success = True
                    # BUG: should break after first successful delivery
                    # Currently sends through ALL channels even after success

            except Exception as e:
                # BUG: failure is not recorded anywhere
                continue

        notification.status = DeliveryStatus.DELIVERED if success else DeliveryStatus.FAILED
        return success

    def get_pending_by_priority(self) -> list[Notification]:
        """Get pending notifications ordered by priority."""
        pending = [n for n in self.notifications.values() if n.status == DeliveryStatus.PENDING]
        # BUG: sorts in wrong order (LOW first instead of HIGH first)
        pending.sort(key=lambda n: n.priority.value)
        return pending


# TODO: Add NotificationQueue with priority
# TODO: Add proper templating with defaults for missing variables
# TODO: Add delivery status tracking with attempt history
# TODO: Add get_delivery_report(notification_id)
