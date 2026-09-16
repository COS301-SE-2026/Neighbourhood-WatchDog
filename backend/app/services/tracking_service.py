import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.tracking import TrackingSighting, TrackingSubject
from app.models.camera import Camera
from app.models.neighbourhood_user import NeighbourhoodRole, NeighbourhoodUser
from app.models.property import Property
from app.schemas.tracking import TrackingSightingResponse, TrackingTimelineData, TrackingTimelineResponse

logger = logging.getLogger(__name__)


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