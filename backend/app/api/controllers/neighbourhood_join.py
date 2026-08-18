from uuid import UUID

from fastapi import APIRouter, Depends, status
from typing import Annotated

from app.auth.dependencies import get_current_user, require_role
from app.core.database import DbSession
from app.schemas.neighbourhood_join import (
    JoinCodeRes,
    JoinNeighbourhoodReq,
    JoinNeighbourhoodRes,
    JoinRequestRes,
    RegenerateJoinCodeRes,
    ResolveJoinRequestReq,
    ResolveJoinRequestRes,
)
from app.services.neighbourhood_join_service import (
    get_join_code_handler,
    list_join_requests_handler,
    regenerate_join_code_handler,
    request_to_join_handler,
    resolve_join_request_handler,
)

router = APIRouter(prefix="/neighbourhood", tags=["neighbourhood"])

@router.post(
    "/join",
    response_model=JoinNeighbourhoodRes,
    status_code=status.HTTP_201_CREATED,
    summary="Request to join a neighbourhood",
    responses={
        400: {"description": "Missing join code"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions to access property"},
        404: {"description": "Invalid join code"},
        409: {"description": "Already have a pending request"},
    },
)
async def join_neighbourhood(
    body: JoinNeighbourhoodReq,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)],
):
    result = await request_to_join_handler(body.join_code, db, claims)
    return JoinNeighbourhoodRes(status=201, message="Join request submitted", data=result)


@router.get(
    "/join-requests/{neighbourhood_id}",
    response_model=list[JoinRequestRes],
    summary="List pending join requests for the admin's neighbourhood",
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "No database session or failed to list join requests"},
    },
)
async def list_join_requests(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)],
):
    return await list_join_requests_handler(neighbourhood_id, db, claims)

@router.patch(
    "/join-requests/{request_id}",
    response_model=ResolveJoinRequestRes,
    summary="Approve or deny a join request",
    responses={
        400: {
            "description": (
                "Missing join request ID or invalid action. "
                "Action must be APPROVE or DENY."
            )
        },
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Join request or user not found"},
        409: {"description": "Join request has already been resolved"},
        500: {
            "description": (
                "No database session or failed to resolve join request"
            )
        },
    },
)
async def resolve_join_request(
    request_id: UUID,
    body: ResolveJoinRequestReq,
    db: DbSession,
    claims: dict,
):
    require_role("NEIGHBOURHOOD_ADMIN")
    result = await resolve_join_request_handler(request_id, body.property_id, body.action, db, claims)
    return ResolveJoinRequestRes(status=200, message="Join request updated", data=result)

@router.patch(
    "/join-code/{neighbourhood_id}",
    response_model=RegenerateJoinCodeRes
)
async def regenerate_join_code(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)]
):
    return await regenerate_join_code_handler(
        neighbourhood_id,
        db,
        claims
    )

@router.get(
    "/join-code/{neighbourhood_id}",
    response_model=JoinCodeRes
)
async def get_join_code(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)]
):
    return await get_join_code_handler(
        neighbourhood_id,
        db, 
        claims
    )