from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import DbSession
from app.models.alert import Alert, DetectionType
from app.models.camera import Camera
from app.models.zone import GeospatialZone
from app.schemas.detection import DetectionIngestReq, DetectionIngestRes
from app.services.alert_service import _build_alert_res
from app.services.notification_service import dispatch_notifications

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
            zone = db.execute(
                select(GeospatialZone).where(GeospatialZone.id == data.zone_id)
            ).scalar_one_or_none()

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
            db.flush()
            alert_created = True
            alert_id = alert.id

        db.commit()

        if alert:
            db.refresh(alert)
            camera = db.execute(
                select(Camera).where(Camera.id == alert.camera_id)
            ).scalar_one_or_none()
            if camera:
                from app.api.controllers.alert import broadcast

                alert_res = _build_alert_res(alert)
                await broadcast(
                    neighbourhood_id=str(camera.neighbourhood_id),
                    message={"event": "alert.new", "payload": alert_res.model_dump(mode="json")},
                )

                await dispatch_notifications(
                    db=db,
                    alert_id=alert.id,
                    camera_id=alert.camera_id,
                    neighbourhood_id=camera.neighbourhood_id,
                    detection_type=data.detection_type,
                    confidence_score=data.confidence_score,
                    frame_timestamp=data.frame_timestamp,
                )

        return DetectionIngestRes(
            status=201,
            message=("Alert created" if alert_created else "Detection did not meet the configured confidence threshold"),
            alert_created=alert_created,
            alert_id=alert_id,
        )
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to ingest detection")
