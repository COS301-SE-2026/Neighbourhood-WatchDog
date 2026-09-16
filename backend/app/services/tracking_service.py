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