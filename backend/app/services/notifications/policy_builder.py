from collections.abc import Callable

from app.services.notifications.channel import NotificationChannel
from app.services.notifications.policy import NotificationPolicy

class NotificationPolicyBuilder:
    def __init__(
        self,
        channels: list[NotificationChannel],
        recipient_resolver: Callable,
        severity_fn: Callable,
    ):
        self.channels = channels
        self.recipient_resolver = recipient_resolver
        self.severity_fn = severity_fn

    async def with_channel(NotificationChannel):
        pass #TODO we finna add to this

    async def with_recipient_resolver(fn):
        pass #TODO: implement

    async def with_severity(fn):
        pass #TODO: implement

    async def build() -> NotificationPolicy:
        pass # TODO: implement