import logging
import math
import os
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.tracking import TrackingSighting, TrackingSubject, APPEARANCE_EMBEDDING_DIMENSION, APPEARANCE_EMBEDDING_MODEL
from app.models.camera import Camera
from app.models.neighbourhood_user import NeighbourhoodRole, NeighbourhoodUser
from app.models.property import Property
from app.schemas.tracking import MatchTrackingEmbeddingRequest, TrackingMatchData, TrackingMatchResponse, TrackingSightingResponse, TrackingTimelineData, TrackingTimelineResponse

logger = logging.getLogger(__name__)

TRACKING_MATCH_MIN_SIMILARITY = float(os.getenv("TRACKING_MATCH_MIN_SIMILARITY", "0.75"))

if not 0.0 <= TRACKING_MATCH_MIN_SIMILARITY <= 1.0:
    raise ValueError("TRACKING_MATCH_MIN_SIMILARITY must be between 0 and 1")



def normalize_appearance_embedding(values: list[float] | None) -> list[float] | None:
    """validate and normalize deeprsort appearance embedding - return json/db unit vector"""

    if values is None:
        return None

    if len(values) != APPEARANCE_EMBEDDING_DIMENSION:
        raise HTTPException(
            status_code=422, 
            detail=f"appearance_embedding must contain exactly {APPEARANCE_EMBEDDING_DIMENSION} values"

        )

    try:
        embedding = [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422, 
            detail="appearance_embedding must contain numeric values"

        ) from exc


    if not all(math.isfinite(value) for value in embedding):
        raise HTTPException(
            status_code=422,
            detail="appearance_embedding must contain only finite values" 

        )

    norm = math.sqrt(sum(value * value for value in embedding))

    if norm <= 0.0:
        raise HTTPException(
            status_code=422,
            detail="appearance_embedding must not be a zero vector"

        )

    return [value / norm for value in embedding]


async def record_tracking_sighting(*, db: AsyncSession, tracking_subject_id: UUID, camera_id: UUID, local_track_id: int, observed_at: datetime, match_confidence: float | None = None) -> TrackingSighting:
    """records a camera sighting for one tracking subject
    this subject is locked, while the alert status and next seq number are checked.
    acknowledged alerts can't get new sightings
    """

    if match_confidence is not None and not 0 <= match_confidence <= 1:
        raise HTTPException(
            status_code=422, 
            detail="match confidence must be between 0 and 1" 
        )


    if local_track_id < 0:
        raise HTTPException(
            status_code=422, 
            detail="local track id cannot be negative"
        )


    try:
        subject_stmt = (
            select(TrackingSubject, Alert)
            .join(Alert, Alert.id == TrackingSubject.alert_id)
            .where(TrackingSubject.id == tracking_subject_id)
            .with_for_update() ##this locks the trackingsubject row while the transaction is running
                                                # ensures that tracking updates for the same subject are handled sequentially

            )      

        subject_result = await db.execute(subject_stmt)
        row = subject_result.one_or_none()

        if row is None:
            raise HTTPException(
                status_code=404, 
                detail="Tracking subject and related Alert not found"

            )

        tracking_subject, parent_alert = row

        if parent_alert.status != "OPEN": # only an OPEN alert can recieve new sightings
            raise HTTPException(
                status_code=409, 
                detail="Tracking sequence has already terminated"
            )


        #calculating the next sequence number
        next_sequence_stmt = select(
            func.coalesce(func.max(TrackingSighting.sequence_no), 0) + 1 #finds the highest sequence number for the subject and adds 1
        ).where(
            TrackingSighting.tracking_subject_id == tracking_subject_id
        )

        next_sequence_result = await db.execute(next_sequence_stmt)
        next_sequence = int(next_sequence_result.scalar_one())

        sighting = TrackingSighting(
            tracking_subject_id=tracking_subject_id, 
            camera_id=camera_id, 
            local_track_id=local_track_id, 
            observed_at=observed_at, 
            sequence_no=next_sequence, 
            match_confidence=match_confidence

        )

        db.add(sighting)
        await db.commit()
        await db.refresh(sighting)

        logger.info(
            "Recorded tracking sighting: subject=%s camera=%s "
            "local_track_id=%s sequence=%s",
            tracking_subject.id,
            camera_id,
            local_track_id,
            next_sequence
             
        )



        return sighting

    except HTTPException:
        raise

    except IntegrityError as exc:

        await db.rollback()

        logger.warning(
            "Could not record duplicate or invalid tracking sighting "
            "for subject=%s: %s",
            tracking_subject_id,
            exc

        )


        raise HTTPException(
            status_code=409,
            detail="Tracking sighting could not be recorded"

        ) from exc



    except Exception as exc:
        await db.rollback()
        logger.exception(
            "Unexpected failure recording tracking sighting "
            "for subject=%s",
            tracking_subject_id

        )


        raise HTTPException(
            status_code=500,
            detail="Failed to record tracking sighting"
        ) from exc


async def match_tracking_embedding(*, db: AsyncSession, body: MatchTrackingEmbeddingRequest, candidate_property_id: UUID) -> TrackingMatchResponse:
    """given a new person's appereance embedding from a camera, find the closest active tracking subject that could be that same person"""


    if body.embedding_model != APPEARANCE_EMBEDDING_MODEL:
        raise HTTPException(
            status_code=422, 
            detail=f"Unsupported appearance embedding model: {body.embedding_model}"
        )

    candidate_embedding = normalize_appearance_embedding(body.appearance_embedding)

    if candidate_embedding is None:
        raise HTTPException(
            status_code=422,
            detail="appearance_embedding is required"

        )

    candidate_camera_result = await db.execute(
        select(Camera, Property)
        .join(Property, Property.id == Camera.property_id)
        .where(Camera.id == body.camera_id)

    )

    candidate_camera_row = candidate_camera_result.one_or_none()

    if candidate_camera_row is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate camera not found"

        )


    candidate_camera, candidate_property = candidate_camera_row

    if candidate_camera.property_id != candidate_property_id:
        raise HTTPException(
            status_code=403,
            detail="The edge agent is not authorized for this camera"

        )

    if candidate_property.neighbourhood_id is None:
        raise HTTPException(
            status_code=403,
            detail="Candidate camera is not associated with a neighbourhood"
            
        )


##authorization check - decide if a user can view a tracking timeline for a neighbourhhod
async def _require_tracking_timeline_access(*, db: AsyncSession, claims: dict, neighbourhood_id: UUID) -> None:
    """only security, neighbourhood admins, and systems admins can see the tracking timeline"""


    if claims.get("custom:role") == "SYSTEM_ADMIN":
        return

    try:
        user_id = UUID(claims["id"])

    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated" 

        ) from exc


    result = await db.execute(
        select(NeighbourhoodUser).where(
            NeighbourhoodUser.user_id == user_id, NeighbourhoodUser.neighbourhood_id == neighbourhood_id, NeighbourhoodUser.role.in_(
                {NeighbourhoodRole.SECURITY_OFFICER, NeighbourhoodRole.NEIGHBOURHOOD_ADMIN}
            )
        )
    )


    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=403, 
            detail="Only authorized officers can view tracking timelines" 

            
        )


async def get_tracking_timeline(*, db: AsyncSession, alert_id: UUID, claims: dict) -> TrackingTimelineResponse:
    """returing ordered movement timeline for one alert"""

    alert_result = await db.execute(
        select(Alert, Camera, Property)
        .join(Camera, Camera.id == Alert.camera_id)
        .join(Property, Property.id == Camera.property_id)
        .where(Alert.id == alert_id)
    )

    alert_row = alert_result.one_or_none()

    if alert_row is None:
        raise HTTPException(
            status_code=404, 
            detail="Alert not found"

        )

    alert, originating_camera, property_obj = alert_row

    if property_obj.neighbourhood_id is None:
        raise HTTPException(
            status_code=403, 
            detail="Alert is not associated with a neighbourhood"

        )

    
    await _require_tracking_timeline_access(db=db, claims=claims, neighbourhood_id=property_obj.neighbourhood_id)

    subject_result = await db.execute(
        select(TrackingSubject)
        .where(TrackingSubject.alert_id == alert_id)
    )

    tracking_subject = subject_result.scalar_one_or_none()
    if tracking_subject is None:
        raise HTTPException(
            status_code=404, 
            detail="Tracking timeline not found"

        )


    sightings_result = db.execute(
        select(TrackingSighting, Camera)
        .join(Camera, Camera.id == TrackingSighting.camera_id)
        .where(TrackingSighting.tracking_subject_id == tracking_subject.id)
        .order_by(
            TrackingSighting.sequence_no.asc(), 
            TrackingSighting.observed_at.asc()
            )
    )


    sightings = [
        TrackingSightingResponse(
            id=sighting.id, 
            camera_id=sighting_camera.id, 
            camera_name=sighting_camera.name, 
            camera_location=sighting_camera.location, 
            local_track_id=sighting.local_track_id,
            observed_at=sighting.observed_at,
            sequence_no=sighting.sequence_no,
            match_confidence=sighting.match_confidence,

            
        )
        for sighting, sighting_camera in sightings_result.all()


    ]


    return TrackingTimelineResponse (
        status=200, 
        message="Tracking timeline retrieved successfully", 
        data=TrackingTimelineData(
            alert_id=alert_id, 
            tracking_subject_id=tracking_subject.id, 
            alert_status=alert.status, 
            sightings=sightings

        )
        
    )