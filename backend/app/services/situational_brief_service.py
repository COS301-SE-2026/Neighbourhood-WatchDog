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



def _build_brief(tracking_subject: TrackingSubject, parent_alert: Alert, source_camera: Camera, source_property: Property, sightings: list[tuple[TrackingSighting, Camera, Property]], trigger: str) -> SituationalBriefData:
    """constructing the situational brief"""

    generated_at = datetime.now(timezone.utc)

    cameras: dict[UUID, SituationalBriefCamera] = {}
    brief_sightings: list[SituationalBriefSighting] = [] 


    #building camera info
    for sighting, camera, property_obj in sightings:

        cameras[camera.id] = SituationalBriefCamera(
            camera_id=camera.id, 
            camera_name=camera.name,
            camera_location=camera.location,
            property_id=property_obj.id

        )


        #building sighting info
        brief_sightings.append(
            SituationalBriefSighting(
                sighting_id=sighting.id,
                sequence_no=sighting.sequence_no,
                camera_id=camera.id,
                camera_name=camera.name,
                camera_location=camera.location,
                property_id=property_obj.id,
                local_track_id=sighting.local_track_id,
                observed_at=sighting.observed_at,
                match_confidence=sighting.match_confidence

            )
        )

    ##finding the last known location
    last_sighting, last_camera, last_property = max(
        sightings,
        key=lambda item: (item[0].observed_at, item[0].sequence_no)
    )

    last_location = SituationalBriefLastKnownLocation(
        camera_id=last_camera.id,
        camera_name=last_camera.name,
        camera_location=last_camera.location,
        property_id=last_property.id,
        observed_at=last_sighting.observed_at

    )


    # building alert info
    alert_data = SituationalBriefAlert(
        alert_id=parent_alert.id,
        detection_type=_enum_value(parent_alert.detection_type),
        confidence_score=parent_alert.confidence_score,
        status=str(parent_alert.status),
        observed_at=parent_alert.frame_timestamp,
        camera_id=source_camera.id,
        camera_name=source_camera.name,
        camera_location=source_camera.location

    )


    #get tracking duration
    first_seen = min(
        sighting.observed_at
        for sighting, _, _ in sightings
    )

    last_seen = max(
        sighting.observed_at
        for sighting, _, _ in sightings
    )

    duration_seconds = max(0, int((last_seen - first_seen).total_seconds()))


    #create the summary
    camera_count = len(cameras)

    summary = (
        f"Tracking subject {tracking_subject.id} was observed across "
        f"{camera_count} camera(s) over approximately {duration_seconds} second(s). "
        f"Last known location: {last_camera.name} ({last_camera.location})."

    )



    return SituationalBriefData(
        tracking_subject_id=tracking_subject.id,
        generated_at=generated_at,
        trigger=trigger,
        summary=summary,
        cameras=list(cameras.values()),
        alerts=[alert_data],
        sightings=brief_sightings,
        last_known_location=last_location

    )


async def maybe_generate_situational_brief(*, db: AsyncSession, tracking_subject_id: UUID) -> SituationalBriefData | None:

    (tracking_subject, parent_alert, source_camera, source_property, sightings) = await _load_context(db, tracking_subject_id)


    #checking if a breif already exists
    if tracking_subject.brief_data:
        return SituationalBriefData.model_validate(tracking_subject.brief_data) #effectively makes the brief cached


    #checking the trigger
    trigger = _get_trigger(parent_alert, sightings)
    if trigger is None:
        return None


    ##if we do have a trigger, then generate a brief
    brief = _build_brief(
        tracking_subject=tracking_subject,
        parent_alert=parent_alert,
        source_camera=source_camera,
        source_property=source_property,
        sightings=sightings,
        trigger=trigger

    )

    #saving it
    tracking_subject.brief_generated_at = brief.generated_at
    tracking_subject.brief_trigger = trigger
    tracking_subject.brief_data = brief.model_dump(mode="json")

    await db.commit()

    return brief