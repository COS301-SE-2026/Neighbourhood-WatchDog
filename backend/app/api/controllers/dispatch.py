from uuid import UUID
from typing import Annotated, Literal
from datetime import datetime

from fastapi import APIRouter, Query

from app.auth.authorization import Claims, NeighbourhoodAdminClaims
from app.core.database import DbSession
from app.schemas.dispatch import AlertDispatchRes, RespondDispatchRes, RespondDispatchReq, DispatchListRes
from app.services.dispatch_service import get_alert_dispatch_handler, respond_to_dispatch_handler, list_neighbourhood_dispatches_handler
from app.models.dispatch import DispatchStatus

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

@router.get(
    "/neighbourhood/{neighbourhood_id}",
    response_model=DispatchListRes,
    status_code=200,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Only neighbourhood admins can list dispatches"},
    },
)
async def list_neighbourhood_dispatches(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: NeighbourhoodAdminClaims,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: DispatchStatus | None = None,
    search_term: Annotated[str | None, Query(max_length=100)] = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    sort_order: Literal["ASC", "DESC"] = "DESC",
):
    return await list_neighbourhood_dispatches_handler(
        neighbourhood_id=neighbourhood_id,
        db=db,
        claims=claims,
        page=page,
        size=size,
        status=status,
        search_term=search_term,
        start_date=start_date,
        end_date=end_date,
        sort_order=sort_order,
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