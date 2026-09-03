import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

import asyncio
import os
import dotenv

import logging
from uuid import UUID
from sqlalchemy import select
from app.core.database import DbSession

from app.models.neighbourhood_user import NeighbourhoodRole, NeighbourhoodUser
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.property import Property
from app.models.user import User
from app.models.camera import Camera

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SMTP_SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SMTP_APP_PASSWORD')
MAX_EMAIL_BATCH_SIZE = int(
    os.getenv("MAX_EMAIL_BATCH_SIZE", "50")
)

CRITICAL_TYPES = {"WEAPON_DETECTED", "FALL_DETECTED"}

def _classify_severity(detection_type: str, confidence_score: float) -> str:
    if detection_type in CRITICAL_TYPES:
        return "CRITICAL"
    elif confidence_score >= 0.65:
        return "HIGH"
    elif confidence_score >= 0.45:
        return "MEDIUM"
    return "LOW"

def should_notify(detection_type: str, confidence_score: float) -> bool:
    severity = _classify_severity(detection_type, confidence_score)
    return severity in ("HIGH", "CRITICAL")

def _format_whatsapp_message(
    severity: str,
    detection_type: str,
    camera_name: str,
    timestamp: str
    
) -> str:
    severity_emoji = "🔴" if severity == "CRITICAL" else "🟡"
    formatted_type = detection_type.replace("_", " ").title()
    return(
        f"{severity_emoji} *{severity} ALERT - Neighbourhood Watchdog*\n\n"
        f"Camera: {camera_name}\n"
        f"Detection: {formatted_type}\n"
        f"Time: {timestamp}\n\n"
        "Open the dashboard to review this alert."
    )

def _send_whatsapp(to_phone: str, message: str) -> tuple[bool, str | None]:
    """Send whatsapp message using twilio snadbox. Recipient must be part of sandbox to receive messages"""
    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

        if not account_sid or not auth_token:
            return False, "Twilio credentials not configured"

        #Ennsures number has whatsapp prefix and +27 country code e.g. 0821234567 -> whatsapp:+27821234567
        normalised = to_phone.strip()
        if not normalised.startswith("whatsapp:"):
            if normalised.startswith("0"):
                normalised = "+27" + normalised[1:]
            if not normalised.startswith("+"):
                normalised = "+" + normalised
            normalised = f"whatsapp:{normalised}"

        client = Client(account_sid, auth_token)
        client.messages.create(
            from_=from_number,
            to=normalised,
            body=message,
        )
        return True, None

    except Exception as e:
        logger.exception(f"WhatsApp send failed to {to_phone}")
        return False, str(e)

def build_alert_email(alert_type: str, camera_name: str, location: str,
                    risk_level: str = "HIGH", dashboard_url: str | None = "https://neighbourhood-watch-dog.vercel.app/auth/login") -> str:
    timestamp = datetime.datetime.now().strftime("%d %b %Y · %H:%M")

    formatted_alert_type = html.escape(alert_type.replace("_", " ").strip().title())
    safe_camera_name = html.escape(camera_name)
    safe_location = html.escape(location)
    safe_risk_level = html.escape(risk_level.upper())

    severity_colours = {
        "CRITICAL": ("#EF4444", "#2A1111"),
        "HIGH": ("#F59E0B", "#2A1D08"),
        "MEDIUM": ("#F59E0B", "#2A1D08"),
        "LOW": ("#6AB0FF", "#10233A"),
    }
    severity_colour, severity_background = severity_colours.get(
        risk_level.upper(), ("#F59E0B", "#2A1D08")
    )

    cta_row = ""
    if dashboard_url:
        safe_dashboard_url = html.escape(dashboard_url, quote=True)
        cta_row = f"""
            <tr>
                <td style="padding-top: 28px;">
                <table role="presentation" cellspacing="0" cellpadding="0" width="100%">
                    <tr>
                    <td align="center" bgcolor="#10B981" style="border-radius: 8px;">
                        <a href="{safe_dashboard_url}"
                            style="display: block; padding: 15px 24px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; font-weight: 700; color: #07130F; text-decoration: none;">
                        View alert details&nbsp; &rarr;
                        </a>
                    </td>
                    </tr>
                </table>
                </td>
            </tr>"""

    return f"""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <title>Neighbourhood WatchDog alert</title>
    <style>
        @media only screen and (max-width: 600px) {{
            .email-shell {{ padding: 20px 12px !important; }}
            .email-card {{ width: 100% !important; }}
            .email-content {{ padding: 28px 24px !important; }}
            .email-footer {{ padding: 0 24px 24px !important; }}
            .detail-column {{ display: block !important; width: 100% !important; padding: 0 0 18px !important; }}
            .timestamp {{ display: block !important; text-align: left !important; padding-top: 10px !important; }}
        }}
    </style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0A0A0A; -webkit-font-smoothing: antialiased;">

    <div style="display: none; max-height: 0; overflow: hidden; opacity: 0; color: transparent;">
        {safe_risk_level} alert at {safe_location}. Review the camera event and coordinate a response.
    </div>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" class="email-shell" style="background-color: #0A0A0A; padding: 40px 20px;">
    <tr>
        <td align="center">

        <table role="presentation" width="560" cellpadding="0" cellspacing="0" class="email-card" style="width: 100%; max-width: 560px; background-color: #141414; border: 1px solid #272727; border-radius: 12px; overflow: hidden;">

            <tr>
            <td style="height: 5px; background-color: {severity_colour}; line-height: 5px; font-size: 5px;">&nbsp;</td>
            </tr>

            <tr>
            <td class="email-content" style="padding: 36px 40px 32px;">

                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 38px;">
                <tr>
                    <td valign="middle" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                        <table role="presentation" cellpadding="0" cellspacing="0">
                        <tr>
                            <td align="center" valign="middle" width="38" height="38" style="width: 38px; height: 38px; border: 1px solid #10B981; border-radius: 10px; color: #10B981; font-size: 11px; font-weight: 800; letter-spacing: -0.5px;">NW</td>
                            <td style="padding-left: 12px; color: #F5F5F5; font-size: 14px; font-weight: 750; line-height: 17px; letter-spacing: 0.4px;">
                                NEIGHBOURHOOD<br><span style="color: #10B981;">WATCHDOG</span>
                            </td>
                        </tr>
                        </table>
                    </td>
                    <td align="right" valign="middle" class="timestamp" style="font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace; color: #8A8A8A; font-size: 11px; line-height: 16px;">
                    {timestamp}
                    </td>
                </tr>
                </table>

                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 26px;">
                <tr>
                    <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                    <span style="display: inline-block; padding: 6px 10px; background-color: {severity_background}; border: 1px solid {severity_colour}; border-radius: 999px; color: {severity_colour}; font-size: 10px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase;">
                        {safe_risk_level} priority
                    </span>
                    <h1 style="margin: 18px 0 10px; color: #F5F5F5; font-size: 28px; font-weight: 700; line-height: 1.25; letter-spacing: -0.5px;">
                        {formatted_alert_type}
                    </h1>
                    <p style="margin: 0; color: #A3A3A3; font-size: 15px; line-height: 23px;">
                        Your neighbourhood watch detected an event that needs attention. Review the details and help coordinate the right response.
                    </p>
                    </td>
                </tr>
                </table>

                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #0D0D0D; border: 1px solid #272727; border-radius: 8px;">
                <tr>
                    <td width="50%" valign="top" class="detail-column" style="padding: 20px 12px 20px 20px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #8A8A8A; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; padding-bottom: 7px;">
                            Seen by
                        </td>
                        </tr>
                        <tr>
                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #F5F5F5; font-size: 14px; font-weight: 600; line-height: 20px;">
                            {safe_camera_name}
                        </td>
                        </tr>
                    </table>
                    </td>

                    <td width="50%" valign="top" class="detail-column" style="padding: 20px 20px 20px 12px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #8A8A8A; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; padding-bottom: 7px;">
                            In your neighbourhood
                        </td>
                        </tr>
                        <tr>
                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #F5F5F5; font-size: 14px; font-weight: 600; line-height: 20px;">
                            {safe_location}
                        </td>
                        </tr>
                    </table>
                    </td>
                </tr>
                </table>

                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                {cta_row}
                </table>

            </td>
            </tr>
            
            <tr>
            <td class="email-footer" style="padding: 0 40px 30px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #777777; font-size: 11px; line-height: 17px; border-top: 1px solid #272727; padding-top: 22px;">
                    <span style="color: #A3A3A3;">Watching together. Responding sooner.</span><br>
                    This alert was sent automatically by Neighbourhood WatchDog. Please do not reply.
                    </td>
                </tr>
                </table>
            </td>
            </tr>

        </table>
        </td>
    </tr>
    </table>
    </body>
    </html>
    """

def send_alert_email(recipient_email: str, alert_type: str, camera_name: str, location: str,
                    risk_level: str = "HIGH", dashboard_url: str | None = "https://neighbourhood-watch-dog.vercel.app/auth/login/")-> tuple[bool, str | None]:

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.error("SMTP_SENDER_EMAIL or SMTP_APP_PASSWORD not configured")
        return False, "SMTP credentials not configured"

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        subject = f"{risk_level} severity alert: {alert_type} at {location}"
        plain_body = (
            f"{alert_type} detected at {camera_name} ({location}).\n"
            f"Risk level: {risk_level}\n"
            f"Please review footage and confirm the response."
        )

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Neighbourhood WatchDog <{SENDER_EMAIL}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(build_alert_email(alert_type, camera_name, location, risk_level, dashboard_url), 'html'))

        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        logger.info('Alert email sent successfully!')

        server.quit()
        return True, None
    except Exception as e:
        logger.exception(f"Error sending alert email to {recipient_email}")
        return False, str(e)


def send_alert_email_bcc(
    recipient_emails: list[str],
    alert_type: str,
    camera_name: str,
    location: str,
    risk_level: str = "HIGH",
    dashboard_url: str | None = "https://neighbourhood-watch-dog.vercel.app/auth/login"
) -> tuple[bool, str | None]:
    if not recipient_emails:
        return False, "No email recipients provided"

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.error("SMTP_SENDER_EMAIL or SMTP_APP_PASSWORD not configured")
        return False, "SMTP credentials not configured"

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        subject = f"{risk_level} severity alert: {alert_type} at {location}"

        plain_body = (
            f"{alert_type} detected at {camera_name} ({location}).\n"
            f"Risk level: {risk_level}\n"
            f"Please review footage"
        ) 

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Neighbourhood WatchDog <{SENDER_EMAIL}>"
        msg['To'] = f"WatchDog Alerts <{SENDER_EMAIL}>"
        msg["Bcc"] = ", ".join(recipient_emails)
        msg['Subject'] = subject

        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(build_alert_email(alert_type, camera_name, location, risk_level, dashboard_url), 'html'))

        server.sendmail(
            SENDER_EMAIL,
            recipient_emails,
            msg.as_string()
        )

        server.quit()

        
        logger.info("Alert email BCC sent to %s recipient(s)", len(recipient_emails))

        return True, None

    except Exception as error:
        logger.exception("Error sending BCC alert email")
        return False, str(error)

def _log_notification(
    db: DbSession,
    alert_id: UUID,
    user_id: UUID,
    channel: NotificationChannel,
    success: bool,
    error_message: str | None,
) -> None:
    db.add(
        Notification(
            alert_id=alert_id,
            user_id=user_id,
            channel=channel,
            status=(
                NotificationStatus.SENT
                if success
                else NotificationStatus.FAILED
            ),
            error_message=error_message,
        )
    )

async def dispatch_notifications(
    db: DbSession,
    alert_id: UUID,
    camera_id: UUID,
    user_ids: list[UUID],
    detection_type: str,
    confidence_score: float,
    frame_timestamp,
) -> None:
    if not should_notify(detection_type, confidence_score):
        logger.info(f"Alert {alert_id}: confidence {confidence_score:.2f} below notification threshold, skipping")
        return

    if os.getenv("NOTIFICATION_ENABLED", "false").lower() != "true":
        logger.info(f"Alert {alert_id}: NOTIFICATION_ENABLED is not 'true', skipping")
        return


    try:
        camera_result = await db.execute(select(Camera).where(Camera.id == camera_id))
        camera = camera_result.scalar_one_or_none()

        if not camera:
            logger.error(f"Camera with id {camera_id} does not exist")
            return

        

        severity = _classify_severity(detection_type, confidence_score)
        recipient_user_ids: set[UUID] = set(user_ids)

        neighbourhood_result = await db.execute(select(Property.neighbourhood_id).where(Property.id == camera.property_id))
        neighbourhood_id = neighbourhood_result.scalar_one_or_none()


        if severity == "CRITICAL" and neighbourhood_id:
            neighbourhood_users_result = await db.execute(
                select(NeighbourhoodUser.user_id).where(
                    NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
                    NeighbourhoodUser.role == NeighbourhoodRole.RESIDENT,
                )
            )

            recipient_user_ids.update(
                neighbourhood_users_result.scalars().all()
            )

        if not recipient_user_ids:
            logger.info(
                "Alert %s: no eligible notification recipients found",
                alert_id,
            )
            return

        users_result = await db.execute(
            select(User).where(User.id.in_(recipient_user_ids))
        )
        users = list(users_result.scalars().all())

        if not users:
            logger.info(
                "Alert %s: recipient IDs did not resolve to users",
                alert_id,
            )
            return

        timestamp_str = (
        frame_timestamp.strftime("%d %b %Y, %H:%M:%S")
        if frame_timestamp
        else "Unknown"
        )

        whatsapp_message = _format_whatsapp_message(
        severity,
        detection_type,
        camera.name,
        timestamp_str,
        )

        logger.info(
            "Alert %s [%s]: notifying %s eligible user(s)",
            alert_id,
            severity,
            len(users),
        )

        await _notify_users(
            db=db,
            alert_id=alert_id,
            users=users,
            whatsapp_message=whatsapp_message,
            detection_type=detection_type,
            camera=camera,
            severity=severity,
        )

        await db.commit()

    except Exception:
        await db.rollback()
        logger.exception(
            "Failed while dispatching notifications for alert %s",
            alert_id,
        )


async def _notify_users_by_whatsapp(
    db: DbSession,
    alert_id: UUID,
    users: list[User],
    whatsapp_message: str
) -> None:
    for user in users:
        if user.phone_number:
            success, error = await asyncio.to_thread(_send_whatsapp, user.phone_number, whatsapp_message)
            _log_notification(db, alert_id, user.id, NotificationChannel.WHATSAPP, success, error)
            if success:
                logger.info(f"Whatsapp sent successfully to user {user.id}")
            else:
                logger.warning(f"WhatsApp failed for user {user.id}: {error}")
        else:
            logger.info(f"User {user.id} has no phone_number, skipping")


async def _notify_users_by_bcc_email(
    db: DbSession,
    alert_id: UUID,
    users: list[User],
    detection_type: str,
    camera: Camera,
    severity: str
) -> None:
    email_users = [
        user
        for user in users
        if user.email
    ]

    for index in range(0, len(email_users), MAX_EMAIL_BATCH_SIZE):
        batch_users = email_users[index:index + MAX_EMAIL_BATCH_SIZE]

        recipient_emails = [
            user.email
            for user in batch_users
            if user.email
        ]


        success, error = await asyncio.to_thread(
            send_alert_email_bcc,
            recipient_emails,
            detection_type,
            camera.name,
            camera.location,
            severity
        )

        for user in batch_users:
            _log_notification(db, alert_id, user.id, NotificationChannel.EMAIL, success, error)

            if success:
                logger.info("BCC email sent successfully to user %s", user.id)
            else:
                logger.warning("BCC email failed for user %s: %s", user.id, error)


async def _notify_users_by_individual_email(
    db: DbSession,
    alert_id: UUID,
    users: list[User],
    detection_type: str,
    camera: Camera,
    severity: str
) -> None:
    for user in users:                
        if user.email:
            success, error = await asyncio.to_thread(send_alert_email, user.email, detection_type, camera.name, camera.location, severity)
            _log_notification(db, alert_id, user.id, NotificationChannel.EMAIL, success, error)
            if success:
                logger.info(f"Email sent successfully to user {user.id}")
            else:
                logger.warning(f"Email failed for user {user.id}: {error}")
        else:
            logger.info(f"User {user.id} has no email, skipping")
async def _notify_users(
    db: DbSession,
    alert_id: UUID,
    users: list[User],
    whatsapp_message: str,
    detection_type: str,
    camera: Camera,
    severity: str,
    email_bcc: bool = False
) -> None:
    
    await _notify_users_by_whatsapp(
        db,
        alert_id,
        users,
        whatsapp_message,
    )

    if email_bcc:
        await _notify_users_by_bcc_email(
            db,
            alert_id,
            users,
            detection_type,
            camera,
            severity,
        )
    else:
        await _notify_users_by_individual_email(
            db,
            alert_id,
            users,
            detection_type,
            camera,
            severity,
        )

        