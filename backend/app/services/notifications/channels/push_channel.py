from uuid import UUID

from app.core.database import DbSession
from app.models.user import User
from app.models.notification import Notification, NotificationChannelEnum, NotificationStatus
from app.services.notifications.channel import NotificationChannel
from app.tasks.push_tasks import send_push_to_users

class PushChannel(NotificationChannel):
    async def send(
        self,
        db: DbSession,
        notification_id: UUID | None,
        recipients: list[User],
        context: dict,
    ):
        recip_ids = [str(user.id) for user in recipients]
        if not recip_ids:
            return

        title, body_template = _PUSHES[context["event_type"]]

        format_context = dict(context)
        if "approved" in format_context:
            format_context["outcome"] = "approved" if format_context["approved"] else "denied"

        send_push_to_users.delay(
            recip_ids,
            title=title,
            body = format_context.get("situational_summary") or body_template.format(**format_context),
            data={"event_type": context["event_type"]}
        )

        for user in recipients:
            db.add(Notification(
                alert_id=notification_id,
                user_id=user.id,
                channel=NotificationChannelEnum.PUSH,
                status=NotificationStatus.SENT,
                error_message=None,
            ))


_PUSHES: dict[str, tuple[str, str]] = {
    # event_type: (title, body template)
    "WEAPON_DETECTED": ("New alert", "{alert_type} detected"), #noqa
    "GENERAL_DETECTION": ("New alert", "{alert_type} detected"),
    "TRACKING_MATCH": ("Cross-property match", "A tracked identity was seen on another property"),
    "PROPERTY_INVITE": ("Property invite", "You've been added to a property"),
    "JOIN_REQUEST": ("New join request", "{property_address} wants to join {neighbourhood_name}"),
    "JOIN_REQUEST_RESOLVED": ("Join request resolved", "Your request for {property_address} was {outcome}"),
    "NEIGHBOURHOOD_BROADCAST": ("New alert", "{alert_type} detected"),
}

