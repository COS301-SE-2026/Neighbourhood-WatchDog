import os
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.camera import Camera
from app.models.neighbourhood_user import NeighbourhoodRole, NeighbourhoodUser
from app.models.property import Property
from app.models.tracking import TrackingSighting, TrackingSubject
from app.schemas.tracking import (
    SituationalBriefAlert,
    SituationalBriefCamera,
    SituationalBriefData,
    SituationalBriefLastKnownLocation,
    SituationalBriefResponse,
    SituationalBriefSighting

)


SITUATIONAL_BRIEF_DURATION_SECONDS = int(os.getenv("SITUATIONAL_BRIEF_DURATION_SECONDS", "60"))
SITUATIONAL_BRIEF_SEVERITY_TYPES = {"WEAPON_DETECTED", "FALL_DETECTED"}


#handle values that might be python enums: detectiontype.weapondetected = weapondetected
def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))



#what caused the trigger to generate a situational briefing
def _get_trigger(alert: Alert, sightings: list[tuple[TrackingSighting, Camera, Property]]) -> str | None:

    detection_type = _enum_value(alert.detection_type)

    if detection_type in SITUATIONAL_BRIEF_SEVERITY_TYPES:
        return "severity_threshold"

    timestamps = [alert.frame_timestamp]

    timestamps.extend(
        sighting.observed_at
        for sighting, _, _ in sightings
    )

    if not timestamps:
        return None

    duration_seconds = (max(timestamps) - min(timestamps)).total_seconds()

    if duration_seconds >= SITUATIONAL_BRIEF_DURATION_SECONDS:
        return "duration_threshold"

    return None


async def _load_context(db: AsyncSession, tracking_subject_id: UUID,) -> tuple[TrackingSubject, Alert, Camera, Property, list[tuple[TrackingSighting, Camera, Property]]]:
    """gathering everything needed to generate the breif"""

    subject_result = await db.execute(
        select(TrackingSubject, Alert, Camera, Property)
        .join(Alert, Alert.id == TrackingSubject.alert_id)
        .join(Camera, Camera.id == Alert.camera_id)
        .join(Property, Property.id == Camera.property_id)
        .where(TrackingSubject.id == tracking_subject_id)

    )

    subject_row = subject_result.one_or_none()

    if subject_row is None:
        raise HTTPException(
            status_code=403, 
            detail="Tracking subject not found"
        )

    (tracking_subject, parent_alert, source_camera, source_property) = subject_row


    # load all sightings
    sightings_result = await db.execute(
        select(TrackingSubject, Camera, Property)
        .join(Camera, Camera.id == TrackingSighting.camera_id)
        .join(Property, Property.id == Camera.property_id)
        .where(TrackingSighting.tracking_subject_id == tracking_subject_id)
        .order_by(TrackingSighting.sequence_no.asc(), TrackingSighting.observed_at.asc())
    )

    sightings = list(sightings_result.all())

    if not sightings:
        raise HTTPException(
            status_code=404, 
            detail="Tracking sightings not found" 
        )

    return (tracking_subject, parent_alert, source_camera, source_property, sightings)
