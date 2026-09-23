from uuid import UUID

from fastapi import APIRouter

from app.auth.authorization import Claims
from app.core.database import DbSession
from app.schemas.dispatch import AlertDispatchRes
from app.services.dispatch_service import get_alert_dispatch_handler

router = APIRouter(prefix="/dispatch", tags=["dispatch"])

@router.get(
    "/alert/{alert_id}",
    response_model=AlertDispatchRes,
    status_code=200,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Only admins and security officers of the alert's neighbourhood can view its dispatch"},
        404: {"description": "Alert not found"},
    }
)
async def get_alert_dispatch(
    alert_id: UUID,
    db: DbSession,
    claims: Claims,
):
    return await get_alert_dispatch_handler(
        alert_id=alert_id,
        db=db,
        claims=claims,
    )