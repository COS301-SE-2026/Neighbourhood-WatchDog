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
    formatted_type = detection_type.replaced("_", " ").title()
    return(
        f"{severity_emoji} *{severity} ALERT - Neighbourhood Watchdog*\n\n"
        f"Camera: {camera_id}\n"
        f"Detection: {formatted_type}\n"
        f"Time: {timestamp}\n\n"
        f"Open the dashboard to review this alert."
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
        logger.error(f"WhatsApp send failed to {to_phone}: {e}")
        return False, str(e)