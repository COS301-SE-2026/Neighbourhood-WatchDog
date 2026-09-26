from uuid import UUID

from app.core.database import DbSession
from app.models.user import User
from app.services.notifications.channel import NotificationChannel
from app.tasks.notification_tasks import send_whatsapp_task

class WhatsAppChannel(NotificationChannel):
    async def send(
        self,
        db: DbSession,
        notification_id: UUID | None,
        recipients: list[User],
        context: dict,
    ):
        msg_template = _WHATSAPP_MESSAGES[context["event_type"]]

        format_context = dict(context)
        if "approved" in format_context:
            format_context["outcome"] = "approved" if format_context["approved"] else "denied"

        message = msg_template.format(**format_context)

        for user in recipients:
            
            if not user.phone_number:
                continue

            send_whatsapp_task.delay(
                str(notification_id) if notification_id else None,
                str(user.id),
                user.phone_number,
                message,
            )


_WHATSAPP_MESSAGES: dict[str, str] = {
    # event_type: (title, body template)
    "WEAPON_DETECTED": "{risk_level} ALERT - Neighbourhood WatchDog\n\nCamera: {camera_name}\nDetection: {alert_type}\nTime: {timestamp}\n\nOpen dashboard to review this alert.", #noqa
    "GENERAL_DETECTION": "{risk_level} ALERT - Neighbourhood WatchDog\n\nCamera: {camera_name}\nDetection: {alert_type}\nTime: {timestamp}\n\nOpen dashboard to review this alert.",
    "TRACKING_MATCH": "CROSS-PROPERTY MATCH - Neighbourhood WatchDog\n\nFrom property: {source_property}\nTo property: {destination_property}\nCamera: {camera_name}\n\nOpen the dashboard to review this match.",
    "PROPERTY_INVITE": "{inviter_name} added you to a property on Neighbourhood WatchDog.\nProperty: {property_address}\nOpen the dashboard: {dashboard_url}",
    "JOIN_REQUEST": "{property_address} has requested to join {neighbourhood_name}. Review it on the dashboard.",
    "JOIN_REQUEST_RESOLVED": "Your request for {property_address} to join {neighbourhood_name} was {outcome}",
    "NEIGHBOURHOOD_BROADCAST": "{risk_level} ALERT - Neighbourhood WatchDog\n\nCamera: {camera_name}\nDetection: {alert_type}\nTime: {timestamp}\n\nOpen dashboard to review this alert.",
}