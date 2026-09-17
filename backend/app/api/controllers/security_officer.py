from fastapi import APIRouter

from app.auth.authorization import Claims
from app.core.database import DbSession
from app.schemas.neighbourhood import (
    UpdateOfficerLocationReq,
    UpdateOfficerLocationRes,
)
from app.services.security_officer_service import update_location_handler

router = APIRouter(prefix="/security-officer", tags=["neighbourhood", "security-officer"])

@router.patch(
    "/update-location",
    response_model=UpdateOfficerLocationReq, # noqa
    status_code=200,
    responses={
        401: {"description": "Invalid or missing authentication token"},
    }
)
async def update_location(
    req: UpdateOfficerLocationReq,
    db: DbSession,
    claims: Claims,
) -> UpdateOfficerLocationRes:
    """Gets the security officer's latest location and updates it in the database"""
    return await update_location_handler(
        req,
        db,
        claims,
    )