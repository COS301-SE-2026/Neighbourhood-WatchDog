from collections.abc import Callable

from app.services.notifications.channel import NotificationChannel
from app.services.notifications.policy import NotificationPolicy

class NotificationPolicyBuilder:
    resolver: Callable = None
    severity_fn: Callable = None

    def __init__(self):
        self.channels = []

    def with_channel(self, channel: NotificationChannel):
        self.channels.append(channel)
        return self

    def with_recipient_resolver(self, fn):
        self.resolver = fn
        return self

    def with_severity(self, fn):
        self.severity_fn = fn
        return self

    def build(self) -> NotificationPolicy:
        return NotificationPolicy(
            channels=self.channels,
            recipient_resolver=self.resolver,
            severity_fn=self.severity_fn
        )