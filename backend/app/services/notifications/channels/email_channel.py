import logging

from uuid import UUID
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.database import DbSession
from app.models.user import User
from app.services.notifications.channel import NotificationChannel
from app.tasks.notification_tasks import send_email_task, send_email_bcc_task
from app.services.notifications.notification_service import MAX_EMAIL_BATCH_SIZE

logger = logging.getLogger(__name__)

_env = Environment(
    loader=FileSystemLoader("app/services/notifications/templates"),
    autoescape=select_autoescape(["html"]),
)

class EmailChannel(NotificationChannel):
    async def send(
        self,
        db: DbSession,
        notification_id: UUID | None,
        recipients: list[User],
        context: dict,
    ):
        template_name, subject = _TEMPLATES[context["event_type"]]
        template = _env.get_template(template_name)
        
        render_context = dict(context)
        if template_name == ALERT_TEMPLATE_FILENAME:
            severity_colour, severity_background = _SEVERITY_COLOURS.get(
                context["risk_level"].upper(), ("#F59E0B", "#2A1D08")
            )
            render_context["severity_colour"] = severity_colour
            render_context["severity_background"] = severity_background
            render_context.setdefault("timestamp", datetime.now().strftime("%d %b %Y %H:%M"))
            
        html_body = template.render(**render_context)
        plain_body = _plain_body(context)
        subject_line = subject.format(**context)

        email_recipients = [user for user in recipients if user.email]
        if not email_recipients:
            return

        if context["event_type"] in _BCC_EVENTS:
            for i in range(0, len(email_recipients), MAX_EMAIL_BATCH_SIZE):
                batch = email_recipients[i:i + MAX_EMAIL_BATCH_SIZE]
                send_email_bcc_task.delay(
                    str(notification_id) if notification_id else None,
                    [str(user.id) for user in batch],
                    [str(user.email) for user in batch],
                    subject_line,
                    html_body,
                    plain_body,
                )
        else:
            for user in recipients:
                if not user.email:
                    continue
                send_email_task.delay(
                    str(notification_id) if notification_id else None,
                    str(user.id),
                    user.email,
                    subject_line,
                    html_body,
                    plain_body,
                )
    

ALERT_TEMPLATE_FILENAME = "alert_email.html.j2"

_TEMPLATES: dict[str, tuple[str, str]] = {
    # event_type: (template filename, subject line)
    "WEAPON_DETECTED": (ALERT_TEMPLATE_FILENAME, "{risk_level} severity alert: {alert_type}"), #noqa
    "GENERAL_DETECTION": (ALERT_TEMPLATE_FILENAME, "{risk_level} severity alert: {alert_type}"),
    "NEIGHBOURHOOD_BROADCAST": (ALERT_TEMPLATE_FILENAME, "{risk_level} severity alert: {alert_type}"),
    "TRACKING_MATCH": (ALERT_TEMPLATE_FILENAME, "Cross-property thread match detected"),
    "PROPERTY_INVITE": ("property_invite_email.html.j2", "You've been added to a property"),
    "JOIN_REQUEST": ("join_request_email.html.j2", "New join request"),
    "JOIN_REQUEST_RESOLVED": ("join_request_email.html.j2", "Your join request has been resolved")
}

_SEVERITY_COLOURS = {
    "CRITICAL": ("#EF4444", "#2A1111"),
    "HIGH": ("#F59E0B", "#2A1D08"),
    "MEDIUM": ("#F59E0B", "#2A1D08"),
    "LOW": ("#6AB0FF", "#10233A"),
}

_BCC_EVENTS: set[str] = {"NEIGHBOURHOOD_BROADCAST"}


def _plain_body(context: dict) -> str:
    event_type = context["event_type"]

    if event_type in ("WEAPON_DETECTED", "GENERAL_DETECTION", "TRACKING_MATCH", "NEIGHBOURHOOD_BROADCAST"):
        return (
            f"{context['alert_type']} detected at {context['camera_name']} ({context['location']}).\n"
            f"Risk level: {context['risk_level']}\n"
            f"Please review footage and confirm the response."
        )

    if event_type == "PROPERTY_INVITE":
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