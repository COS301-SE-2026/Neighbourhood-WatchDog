from collections.abc import Callable

from app.services.notifications.channel import NotificationChannel

class NotificationPolicyBuilder:
    def __init__(
        self,
        channels: list[NotificationChannel],
        recipient_resolver: Callable,
        severity_fn: Callable | None = None,
    ):
        pass