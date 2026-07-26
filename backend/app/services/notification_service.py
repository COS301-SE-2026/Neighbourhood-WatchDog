import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

import os
import dotenv

import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.user import User, UserRole
from app.models.camera import Camera
from app.models.property_user import PropertyUser

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SMTP_SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SMTP_APP_PASSWORD')

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
                      risk_level: str = "HIGH", dashboard_url: str | None = None) -> str:
    timestamp = datetime.datetime.now().strftime("%d %b %Y · %H:%M")
    
    cta_row = ""
    if dashboard_url:
        cta_row = f"""
            <tr>
              <td style="padding-top: 32px;">
                <table role="presentation" cellspacing="0" cellpadding="0">
                  <tr>
                    <td align="center" bgcolor="#10B981">
                      <a href="{dashboard_url}" 
                         style="display: inline-block; padding: 14px 28px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; color: #000000; text-decoration: none; letter-spacing: 0.5px; text-transform: uppercase;">
                        Review Alerts &rarr;
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
  <title>WatchDog Alert</title>
</head>
<body style="margin: 0; padding: 0; background-color: #000000; -webkit-font-smoothing: antialiased;">
  
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #000000; padding: 40px 20px;">
    <tr>
      <td align="center">
        
        <!-- Main Card: Darker, subtle border, sharp edges -->
        <table role="presentation" width="500" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; border: 1px solid #1f1f1f;">
          
          <!-- Industrial Top Accent -->
          <tr>
            <td style="height: 4px; background-color: #10B981; line-height: 4px; font-size: 4px;">&nbsp;</td>
          </tr>

          <!-- Single Padded Content Area -->
          <tr>
            <td style="padding: 40px;">
              
              <!-- App Header -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                <tr>
                  <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #ffffff; font-size: 14px; font-weight: 700; letter-spacing: 2px;">
                    <span style="color: #10B981; margin-right: 4px;">&#9632;</span> WATCHDOG
                  </td>
                  <td align="right" style="font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace; color: #555555; font-size: 12px;">
                    {timestamp}
                  </td>
                </tr>
              </table>

              <!-- Alert Headline -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                <tr>
                  <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                    <div style="color: #10B981; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px;">
                      {risk_level} Priority Alert
                    </div>
                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; line-height: 1.2; letter-spacing: -0.5px;">
                      {alert_type}
                    </h1>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                <tr><td style="border-top: 1px solid #1f1f1f;"></td></tr>
              </table>

              <!-- Clean Data Grid -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <!-- Left Column -->
                  <td width="50%" valign="top" style="padding-right: 20px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #666666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; padding-bottom: 4px;">
                          Camera Source
                        </td>
                      </tr>
                      <tr>
                        <td style="font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace; color: #ffffff; font-size: 14px;">
                          {camera_name}
                        </td>
                      </tr>
                    </table>
                  </td>
                  
                  <!-- Right Column -->
                  <td width="50%" valign="top">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #666666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; padding-bottom: 4px;">
                          Zone Location
                        </td>
                      </tr>
                      <tr>
                        <td style="font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace; color: #ffffff; font-size: 14px;">
                          {location}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- CTA Row -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                {cta_row}
              </table>

            </td>
          </tr>
          
          <!-- Minimal Footer -->
          <tr>
            <td style="padding: 0 40px 32px 40px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #444444; font-size: 11px; border-top: 1px solid #1f1f1f; padding-top: 24px;">
                    System generated by WatchDog Security Node. Do not reply to this email.
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
                      risk_level: str = "HIGH", dashboard_url: str | None = None)-> tuple[bool, str | None]:
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

def _log_notification(
        db: Session,
        alert_id: UUID,
        user_id: UUID,
        channel: NotificationChannel,
        success: bool,
        error_message: str | None,
) -> None:
    try:
        record = Notification(
            alert_id=alert_id,
            user_id=user_id,
            channel=channel.value,
            status=NotificationStatus.SENT.value if success else NotificationStatus.FAILED.value,
            error_message=error_message,
        )
        db.add(record)
        db.commit()
    except Exception:
        logger.exception("Failed to log notification record")
        db.rollback()

async def dispatch_notifications(
        db: Session,
        alert_id: UUID,
        camera_id: UUID,
        neighbourhood_id: UUID,
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

    camera = db.execute(select(Camera).where(Camera.id == camera_id)).scalar_one_or_none()

    if not camera:
        logger.error(f"Camera with id {camera_id} does not exist")
        return

    severity = _classify_severity(detection_type, confidence_score)
    timestamp_str = frame_timestamp.strftime("%d %b %Y, %H:%M:%S") if frame_timestamp else "Unknown"
    whatsapp_message = _format_whatsapp_message(severity, detection_type, camera.name, timestamp_str)


    if severity == "CRITICAL":
        try:
            residents = db.execute(
                select(User).where(User.neighbourhood_id == neighbourhood_id, User.role == UserRole.RESIDENT)
            ).scalars().all()
        except Exception:
            logger.exception(f"Failed to fetch residents for neighbourhood {neighbourhood_id}")
            return

        if not residents:
            logger.info(f"Alert {alert_id}: no residents found in neighbourhood {neighbourhood_id}.")

        logger.info(f"Alert {alert_id} [{severity}]: notifying {len(residents)} resident(s) via WhatsApp & Email")
        _notify_users(db, alert_id, residents, whatsapp_message, detection_type, camera, severity)

    else:
        users = db.execute(
            select(User).join(PropertyUser, PropertyUser.user_id == User.id)
            .where(PropertyUser.property_id == camera.property_id)
        ).scalars().all()

        logger.info(f"Alert {alert_id} [{severity}]: notifying {len(users)} property resident(s) via WhatsApp & Email")
        _notify_users(db, alert_id, users, whatsapp_message, detection_type, camera, severity)


def _notify_users(
        db: Session,
        alert_id: UUID,
        users: list[User],
        whatsapp_message: str,
        detection_type: str,
        camera: Camera,
        severity: str,
) -> None:
    for user in users:
        if user.phone_number:
            success, error = _send_whatsapp(user.phone_number, whatsapp_message)
            _log_notification(db, alert_id, user.id, NotificationChannel.WHATSAPP, success, error)
            if not success:
                logger.warning(f"WhatsApp failed for user {user.id}: {error}")
            else:
                logger.info(f"Whatsapp sent successfully to user {user.id}")
        else:
            logger.info(f"User {user.id} has no phone_number, skipping")

        if user.email:
            success, error = send_alert_email(user.email, detection_type, camera.name, camera.location, severity)
            _log_notification(db, alert_id, user.id, NotificationChannel.EMAIL, success, error)
            if not success:
                logger.warning(f"Email failed for user {user.id}: {error}")
        else:
            logger.info(f"User {user.id} has no email, skipping")