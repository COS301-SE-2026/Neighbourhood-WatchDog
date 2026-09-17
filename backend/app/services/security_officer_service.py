import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from geoalchemy2.elements import WKTElement

from app.auth.authorization import Claims
from app.core.database import DbSession
from app.models.security_officer import SecurityOfficer
from app.models.neighbourhood_user import NeighbourhoodUser
from app.models.user import User
from app.schemas.neighbourhood import (
    UpdateOfficerLocationReq,
    UpdateOfficerLocationRes,
)

logger = logging.getLogger(__name__)

STALE_LOCATION_THRESHOLD_SECONDS = 120

def is_location_stale(location_updated_at: datetime | None ) -> bool:
    if location_updated_at is None:
        return True
    age = (datetime.now(timezone.utc) - location_updated_at).total_seconds()
    return age > STALE_LOCATION_THRESHOLD_SECONDS

async def update_location_handler(
    req: UpdateOfficerLocationReq,
    db: DbSession,
    claims: Claims,
) -> UpdateOfficerLocationRes:
    """The handler function which takes the longitude and latitude in the 
       req and uses them to update the officer's latest position"""

    long = req.longitude
    lat = req.latitude
    neighbourhood_id = req.neighbourhood_id

    if not claims:
        logger.warning("create_property called with no claims")
        raise HTTPException(401, "Not authenticated")
    
    stmt = (
        select(SecurityOfficer) # this is what deals with the validation ensuring that the person is an officer
        .join(NeighbourhoodUser)
        .join(User)
        .where(User.cognito_sub == claims['sub'])
        .where(NeighbourhoodUser.neighbourhood_id == neighbourhood_id)
    )
    result = await db.execute(stmt)
    officer_obj = result.scalars().first() 

    if officer_obj is None:
        logger.warning("update_location_handler Security officer not found. Failed for user with claim, claims=%s", claims)
        raise HTTPException(404, "Security officer not found")
    
    try:
        officer_obj.last_known_location = WKTElement(f"POINT({long} {lat})", srid=4326)
        officer_obj.location_updated_at = datetime.now(timezone.utc)

        await db.commit()
    except Exception:
        await db.rollback()
        logger.warning("update_location_handler failed for officer with claim, claims=%s", claims)
        raise HTTPException(500, "Failed to update security officer's location")

    logger.info("update_location_handler successfully updated the officer with claim, claims=%s's ", claims)
    return UpdateOfficerLocationRes(
        status=200,
        message="Successfully updated security officer's location",
    )