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
from app.models.tracking import TrackingSubject, TrackingSighting
from app.services.tracking_service import normalize_appearance_embedding
from app.services.incident_service import create_incident_for_alert, find_active_incident_for_embedding
from app.schemas.notification import EventType


logger = logging.getLogger(__name__)

SENSITIVITY_THRESHOLDS: dict[str, float] = {
    "LOW": 0.80,
    "MEDIUM": 0.65,
    "HIGH": 0.50,
    "CRITICAL": 0.35,
}

DEFAULT_THRESHOLD = 0.30

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
        tracking_subject = None
        clip_required = False
        matched_incident = None
        neighbourhood_id = None
        if data.local_track_id is not None and data.appearance_embedding is not None:
            camera_for_match_result = await db.execute(
                select(Camera)
                .options(joinedload(Camera.property))
                .where(Camera.id == data.camera_id)
            )
            camera_for_match = camera_for_match_result.scalar_one_or_none()

            neighbourhood_id = (
                camera_for_match.property.neighbourhood_id
                if camera_for_match is not None and camera_for_match.property is not None
                else None
            )

        if (
            data.local_track_id is not None
            and data.appearance_embedding is not None
            and neighbourhood_id is not None
        ):
            candidate_embedding = normalize_appearance_embedding(data.appearance_embedding)

            matched_incident = await find_active_incident_for_embedding(
                db=db,
                neighbourhood_id=neighbourhood_id,
                embedding=candidate_embedding,
                embedding_model=data.embedding_model,
            )

        if matched_incident is not None:
            # A person already tracked by an active incident was seen
            # again - bypasses the normal confidence threshold, since we
            # already know who they are from a strong embedding match.
            existing_stmt = (
                select(Alert)
                .where(
                    Alert.incident_id == matched_incident.id,
                    Alert.camera_id == data.camera_id,
                )
                .order_by(Alert.frame_timestamp.desc())
                .limit(1)
            )
            existing_result = await db.execute(existing_stmt)
            existing_alert = existing_result.scalar_one_or_none()

            if existing_alert is not None:
                matched_incident.last_seen_at = data.frame_timestamp
                await db.commit()

                return DetectionIngestRes(
                    status=201,
                    message="Detection matched an existing tracked incident",
                    alert_created=False,
                    alert_id=existing_alert.id,
                    clip_required=not bool(
                        getattr(existing_alert, "clip_s3_key", None)
                    ),
                )

            alert = Alert(
                camera_id=data.camera_id,
                frame_timestamp=data.frame_timestamp,
                detection_type=data.detection_type,
                confidence_score=data.confidence_score,
                thumbnail_url=data.thumbnail_url,
                processed=True,
                status="OPEN",
            )
            db.add(alert)
            await db.flush()
            alert_created = True
            alert_id = alert.id
            clip_required = True

            alert.incident_id = matched_incident.id
            alert.incident = matched_incident
            matched_incident.last_seen_at = data.frame_timestamp

            tracking_subject = matched_incident.tracking_subject

            if tracking_subject is not None:
                db.add(TrackingSighting(
                    tracking_subject_id=tracking_subject.id,
                    camera_id=alert.camera_id,
                    local_track_id=data.local_track_id,
                    observed_at=alert.frame_timestamp,
                    sequence_no=1,
                    match_confidence=None,
                ))

        elif data.confidence_score >= threshold:
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
            clip_required = True

            await create_incident_for_alert(db=db, alert=alert)

            if data.local_track_id is not None:
                reference_embedding = normalize_appearance_embedding(data.appearance_embedding)

                tracking_subject = TrackingSubject(
                    alert_id=alert.id,
                    reference_embedding=reference_embedding,
                    embedding_model=data.embedding_model,
                )
                db.add(tracking_subject)
                await db.flush()

                db.add(TrackingSighting(
                    tracking_subject_id=tracking_subject.id,
                    camera_id=alert.camera_id,
                    local_track_id=data.local_track_id,
                    observed_at=alert.frame_timestamp,
                    sequence_no=1,
                    match_confidence=None,
                ))

        await db.commit()

        if alert:
            await db.refresh(alert)
            alert.tracking_subject = tracking_subject
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
            clip_required=clip_required,
        )
    except HTTPException as he:
        raise he
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Failed to ingest detection")
