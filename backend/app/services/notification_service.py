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