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