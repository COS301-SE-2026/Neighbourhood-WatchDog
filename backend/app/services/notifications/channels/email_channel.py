from uuid import UUID
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.database import DbSession
from app.models.user import User
from app.services.notifications.channel import NotificationChannel
from app.tasks.notification_tasks import send_email_task

_env = Environment(
    loader=FileSystemLoader("app/services/notifications/templates"),
    autoescape=select_autoescape(["html"]),
)
ALERT_TEMPLATE_FILENAME = "alert_email.html.j2"

_TEMPLATES: dict[str, tuple[str, str]] = {
    # event_type: (template filename, subject line)
    "WEAPON_DETECTED": (ALERT_TEMPLATE_FILENAME, "{risk_level} severity alert: {alert_type}"),
    "GENERAL_DETECTION": (ALERT_TEMPLATE_FILENAME, "{risk_level} severity alert: {alert_type}"),
    "TRACKING_MATCH": (ALERT_TEMPLATE_FILENAME, "Cross-property thread match detected"),
    "PROPERTY_INVITE": ("property_invite_email.html.j2", "You've been added to a property"),
    "JOIN_REQUEST": ("join_request_email.html.j2", "New join request"),
    "JOIN_REQUEST_RESOLVED": ("join_request_email.html.j2", "Your join request has been resolved")
}

def _plain_body(context: dict) -> str:
    event_type = context["event_type"]

    if event_type in ("WEAPON_DETECTED", "GENERAL_DETECTION", "TRACKING_MATCH"):
        return (
            f"{context['alert_type']} detected at {context['camera_name']} ({context['location']}).\n"
            f"Risk level: {context['risk_level']}\n"
            f"Please review footage and confirm the response."
        )

    if event_type in ("WEAPON_DETECTED", "GENERAL_DETECTION", "TRACKING_MATCH"):
        return (
            f"{context['inviter_name']} added you to a property on Neighbourhood WatchDog. \n\n"
            f"Property: {context['property_address']}\n\n"
            f"Open the dashboard to view it: {context['dashboard_url']}"
        )
                
    if event_type == "JOIN_REQUEST":
        return (
            f"{context['property_address']} has request to join {context['neighbourhood_name']}.\n"
            f"Please the request to approve or deny it: {context['dashboard_url']}."
        )

    if event_type == "JOIN_REQUEST_RESOLVED":
        outcome = "approved" if context["approved"] else "denied"
        return (
            f"Your request for {context['property_address']} to join {context['neighbourhood_name']}"
            f"was {outcome}.."
        )

    raise ValueError(f"No plain-body handler for event type: {event_type}")

class EmailChannel(NotificationChannel):
    async def send(
        self,
        db: DbSession,
        notification_id: UUID,
        recipients: list[User],
        context: dict,
    ):
        template_name, subject = _TEMPLATES[context["event_type"]]
        template = _env.get_template(template_name)
        html_body = template.render(**context)
        plain_body = _plain_body(context)

        for user in recipients:
            if not user.email:
                continue
            send_email_task.delay(
                str(notification_id) if notification_id else None,
                str(user.id),
                user.email,
                subject.format(**context),
                html_body,
                plain_body,
            )