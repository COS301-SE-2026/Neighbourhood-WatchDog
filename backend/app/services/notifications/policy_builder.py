from collections.abc import Callable
from typing import Optional
from app.services.notifications.channel import NotificationChannel
from app.services.notifications.policy import NotificationPolicy

class NotificationPolicyBuilder:
    resolver: Optional[Callable] = None
    severity_fn: Optional[Callable] = None

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
        if self.resolver is None:
            raise ValueError("recipient_resolver must be set before building a NotificationPolicy")


        return NotificationPolicy(
            channels=self.channels,
            recipient_resolver=self.resolver,
            severity_fn=self.severity_fn
        )