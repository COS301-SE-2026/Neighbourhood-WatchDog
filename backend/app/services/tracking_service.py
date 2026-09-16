import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.tracking import TrackingSighting, TrackingSubject


logger = logging.getLogger(__name__)


async def record_tracking_sighting(*, db: AsyncSession, tracking_subject_id: UUID, camera_id: UUID, local_track_id: int, observed_at: datetime, match_conf: float | None = None) -> TrackingSighting:
    """records a camera sighting for one tracking subject
    this subject is locked, while the alert status and next seq number are checked.
    acknowledged alerts can't get new sightings
    """

    if match_conf is not None and (match_conf < 0 or match_conf > 1):
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
            match_confidence=match_conf

        )

        db.add(sighting)
        await db.commit()
        await db.refresh(sighting)

        

    except HTTPException:
        raise

