import logging
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.core.database import DbSession
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.zone import GeospatialZone
from app.schemas.detection import DetectionIngestReq, DetectionIngestRes
from app.services.alert_service import _build_alert_res
from app.services.dispatch_service import dispatch_alert
from app.services.notifications.factory import NotificationPolicyFactory
from app.schemas.notification import EventType


logger = logging.getLogger(__name__)

SENSITIVITY_THRESHOLDS: dict[str, float] = {
    "LOW": 0.80,
    "MEDIUM": 0.65,
    "HIGH": 0.50,
    "CRITICAL": 0.35,
}

DEFAULT_THRESHOLD = 0.65
VALID_DETECTIONS = {
    "HUMAN_PRESENCE",
    "LOITERING",
    "PERIMETER_SCAN",
    "WEAPON_DETECTED",
    "FALL_DETECTED",
}


def _get_threshold(zone: GeospatialZone | None) -> float:
    if not zone:
        return DEFAULT_THRESHOLD

    level = zone.sensitivity_level
    if hasattr(level, "value"):
        level = level.value

    return SENSITIVITY_THRESHOLDS.get(str(level), DEFAULT_THRESHOLD)


async def ingest_detection_handler(data: DetectionIngestReq, db: DbSession, claims: dict) -> DetectionIngestRes:
    if not db:
        raise HTTPException(500, "No database session")
    if not claims:
        raise HTTPException(401, "Not authenticated")
    if data.detection_type not in VALID_DETECTIONS:
        raise HTTPException(400, "Invalid detection type")
    if data.confidence_score < 0.0 or data.confidence_score > 1.0:
        raise HTTPException(400, "Confidence score must be between 0 and 1")

    try:
        zone = None
        if data.zone_id:
            zone_result = await db.execute(
                select(GeospatialZone).where(GeospatialZone.id == data.zone_id)
            )
            zone = zone_result.scalar_one_or_none()

        threshold = _get_threshold(zone)


        alert_created = False
        alert_id = None
        alert = None

        if data.confidence_score >= threshold:
            alert = Alert(
                camera_id=data.camera_id,
                frame_timestamp=data.frame_timestamp,
                detection_type=data.detection_type,
                confidence_score=data.confidence_score,
                thumbnail_url=data.thumbnail_url,
                processed=True,
                status="OPEN"
            )
            db.add(alert)
            await db.flush()
            alert_created = True
            alert_id = alert.id

        await db.commit()

        if alert:
            await db.refresh(alert)
            camera_result = await db.execute(
                select(Camera)
                .options(joinedload(Camera.property))
                .where(Camera.id == alert.camera_id)
            )
            camera = camera_result.scalar_one_or_none()
            if camera:

                event_type = "WEAPON_DETECTED" if data.detection_type == "WEAPON_DETECTED" else "GENERAL_DETECTION"
                event_context = {
                    "event_type": event_type,
                    "notification_source_id": alert.id,
                    "neighbourhood_id": camera.property.neighbourhood_id if camera.property else None,
                    "property_id": camera.property_id,
                    "alert_type": data.detection_type,
                    "camera_name": camera.name,
                    "location": camera.location,
                    "risk_level": "CRITICAL" if event_type == "WEAPON_DETECTED" else "MEDIUM",
                    "timestamp": data.frame_timestamp.strftime("%d %b %Y %H:%M"),
                    "websocket_payload": _build_alert_res(alert).model_dump(mode="json"),
                }

                await (NotificationPolicyFactory
                    .get(EventType(event_context["event_type"]))
                    .notify(db, event_context))

                try:
                    await dispatch_alert(db, alert.id)
                except Exception:
                    logger.exception("Dispatch failed for alert %s", alert.id)

        return DetectionIngestRes(
            status=201,
            message=("Alert created" if alert_created else "Detection did not meet the configured confidence threshold"),
            alert_created=alert_created,
            alert_id=alert_id,
        )
    except HTTPException as he:
        raise he
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Failed to ingest detection")
