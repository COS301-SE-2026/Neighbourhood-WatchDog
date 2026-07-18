import os
import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

def _classify_severity(confidence_score: float) -> str:
    if confidence_score >= 0.85:
        return "CRITICAL"
    elif confidence_score >= 0.65:
        return "HIGH"
    elif confidence_score >= 0.45:
        return "MEDIUM"
    return "LOW"

def should_notify(confidence_score: float) -> bool:
    severity = _classify_severity(confidence_score)
    return severity in ("HIGH", "CRITICAL")

def _format_whatsapp_message(
        severity: str,
        detection_type: str,
        camera_id: str,
        timestamp: str,
) -> str:
    severity_emoji = "🔴" if severity == "CRITICAL" else "🟡"
    formatted_type = detection_type.replace("_", " ").title()
    return(
        f"{severity_emoji} *{severity} ALERT - Neighbourhood Watchdog*\n\n"
        f"Camera: {camera_id}\n"
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
        logger.exception(f"Failed to log notification record")
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
    if not should_notify(confidence_score):
        logger.info(f"Alert {alert_id}: confidence {confidence_score:.2f} below notification threshold, skipping")
        return
    
    if os.getenv("NOTIFICATION_ENABLED", "false").lower() != "true":
        logger.info(f"Alert {alert_id}: NOTIFICATION_ENABLED is not 'true', skipping")
        return
    
    severity = _classify_severity(confidence_score)
    timestamp_str = frame_timestamp.strftime("%d %b %Y, %H:%M:%S") if frame_timestamp else "Unknown"
    whatsapp_message = _format_whatsapp_message(severity, detection_type, str(camera_id), timestamp_str)

    try:
        residents = db.execute(select(User).where(User.neighbourhood_id == neighbourhood_id, User.role == UserRole.RESIDENT,)).scalars().all()
    except Exception:
        logger.exception(f"Failed to fetch residents for neighbourhood {neighbourhood_id}")
        return
    
    if not residents:
        logger.info(f"Alert {alert_id}: no residents found in neighbourhood {neighbourhood_id}.")

    logger.info(f"Alert {alert_id} [{severity}]: notifying {len(residents)} resident(s) via WhatsApp")

    for user in residents:
        if user.phone_number:
            success, error = _send_whatsapp(user.phone_number, whatsapp_message)
            _log_notification(db, alert_id, user.id, NotificationChannel.WHATSAPP, success, error)

            if not success:
                logger.warning(f"WhatsApp failed for user {user.id}: {error}")
            else:
                logger.info(f"Whatsapp sent successfully to user {user.id}")
        else:
            logger.info(f"User {user.id} has no phone_number, skipping")