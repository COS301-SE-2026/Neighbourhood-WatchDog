import logging

from collections.abc import Callable

from app.core.database import DbSession
from app.services.notifications.channel import NotificationChannel

logger = logging.getLogger(__name__)

class NotificationPolicy:
    def __init__(
        self,
        channels: list[NotificationChannel],
        recipient_resolver: Callable,
        severity_fn: Callable | None = None,
    ):
        self.channels = channels
        self.recipient_resolver = recipient_resolver
        self.severity_fn = severity_fn

    async def notify(
        self,
        db: DbSession,
        event_context: dict,
    ) -> None:
        recipients = await self.recipient_resolver(db, event_context)
        if not recipients:
            return

        for channel in self.channels:
            try:
                await channel.send(
                    db, 
                    event_context["notification_source_id"], 
                    recipients, 
                    event_context,
                )
            except Exception:
                logger.exception("NotificationPolicy.notify failed to send.")

    