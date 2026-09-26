from uuid import UUID

from app.core.database import DbSession
from app.models.user import User
from app.models.notification import Notification, NotificationChannelEnum, NotificationStatus
from app.services.notifications.channel import NotificationChannel
from app.schemas.notification import EventType
from app.websocket.manager import ConnectionManager

_manager = ConnectionManager()

class WebSocketChannel(NotificationChannel):
    async def send(
        self,
        db: DbSession,
        notification_id: UUID | None,
        recipients: list[User],
        context: dict,
    ):

        if context["event_type"] in {EventType.PROPERTY_INVITE, EventType.JOIN_REQUEST, EventType.JOIN_REQUEST_RESOLVED }:
            return
 
        recipient_ids = [str(user.id) for user in recipients]

        if not recipient_ids:
            return

        event = _WEBSOCKET_EVENTS[context["event_type"]]

        await db.commit()
        await db.close()

        await _manager.broadcast(
            recipient_ids,
            {
                "event": event,
                "payload": context["websocket_payload"]
            }
        )

        for user in recipients:
            db.add(Notification(
                alert_id=notification_id,
                user_id=user.id,
                channel=NotificationChannelEnum.WEBSOCKET,
                status=NotificationStatus.SENT,
                error_message=None,
            ))
        await db.commit()


_WEBSOCKET_EVENTS: dict[str, str] = {
    "WEAPON_DETECTED": "alert.new",
    "GENERAL_DETECTION": "alert.new",
    "TRACKING_MATCH": "tracking.sighting",
    "NEIGHBOURHOOD_BROADCAST": "alert.broadcast",
    # there is no frontend handler for these so I wont include them rn:
    # - PROPERTY_INVITE
    # - JOIN_REQUEST
    # - JOIN_REQUEST_RESOLVED
}