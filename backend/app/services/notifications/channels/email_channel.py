from uuid import UUID

from app.core.database import DbSession
from app.models.user import User
from app.services.notifications.channel import NotificationChannel

class EmailChannel(NotificationChannel):
    async def send(
        self,
        db: DbSession,
        notification_id: UUID,
        recipients: list[User],
        context: dict,
    ):
        pass #TODO: implement. This would add it to the queue