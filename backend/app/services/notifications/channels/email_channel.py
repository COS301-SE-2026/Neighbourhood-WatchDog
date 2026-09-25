from uuid import UUID
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.database import DbSession
from app.models.user import User
from app.services.notifications.channel import NotificationChannel

_env = Environment(
    loader=FileSystemLoader("app/services/notifications/templates"),
    autoescape=select_autoescape(["html"]),
)

class EmailChannel(NotificationChannel):
    async def send(
        self,
        db: DbSession,
        notification_id: UUID,
        recipients: list[User],
        context: dict,
    ):
        #TODO: implement. This would add it to the queue
        pass 