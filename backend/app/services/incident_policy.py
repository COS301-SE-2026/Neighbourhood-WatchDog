"""Shared policy constants and query builders for incident tracking."""

import os
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from app.models.alert import Alert, AlertStatus, DetectionType


ACTIVE_ALERT_STATUSES = (
    AlertStatus.OPEN.value,
    AlertStatus.ACKNOWLEDGED.value,
    AlertStatus.CONFIRMED.value,
)

INCIDENT_MATCH_WINDOW_SECONDS = int(
    os.getenv("INCIDENT_MATCH_WINDOW_SECONDS", "300")
)
TRACKED_ALERT_DUPLICATE_WINDOW_SECONDS = int(
    os.getenv("TRACKED_ALERT_DUPLICATE_WINDOW_SECONDS", "30")
)


def tracked_alert_duplicate_stmt(
    *,
    incident_id: UUID,
    camera_id: UUID,
    detection_type: DetectionType | str,
    observed_at: datetime,
):
    """Find a recent active same-type alert for this incident and camera."""
    duplicate_start = observed_at - timedelta(
        seconds=TRACKED_ALERT_DUPLICATE_WINDOW_SECONDS
    )
    return (
        select(Alert)
        .where(
            Alert.incident_id == incident_id,
            Alert.camera_id == camera_id,
            Alert.detection_type == detection_type,
            Alert.status.in_(ACTIVE_ALERT_STATUSES),
            Alert.frame_timestamp >= duplicate_start,
            Alert.frame_timestamp <= observed_at,
        )
        .order_by(Alert.frame_timestamp.desc())
        .limit(1)
    )
