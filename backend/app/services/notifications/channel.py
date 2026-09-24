from abc import ABC, abstractmethod
from uuid import UUID

from app.core.database import DbSession
from app.models.user import User

class NotificationChannel(ABC):
    """The abstract parent class for the notifcation channels"""        
    @abstractmethod
    async def send(
        self,
        db: DbSession,
        notification_id: UUID,
        recipients: list[User],
        context: dict,
    ) -> None:
        pass

