from uuid import UUID

from fastapi import APIRouter

from app.auth.authorization import Claims
from app.core.database import DbSession
from app.schemas.dispatch import AlertDispatchRes, RespondDispatchRes, RespondDispatchReq
from app.services.dispatch_service import get_alert_dispatch_handler, respond_to_dispatch_handler

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

@router.post(
    "/{dispatch_id}/respond",
    response_model=RespondDispatchRes,
    status_code=200,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "This dispatch request was not sent to the authenticated officer"},
        404: {"description": "Dispatch request not found"},
        409: {"description": "Request already assigned, responded to or expired"},
    }
)
async def respond_to_dispatch(
    dispatch_id: UUID,
    body: RespondDispatchReq,
    db: DbSession,
    claims: Claims,
):
    return await respond_to_dispatch_handler(
        dispatch_id=dispatch_id,
        action=body.action,
        db=db,
        claims=claims,
    )