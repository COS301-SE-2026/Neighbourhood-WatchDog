from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_role
from app.core.database import DbSession
from app.schemas.neighbourhood_join import (
    JoinNeighbourhoodReq,
    JoinNeighbourhoodRes,
    JoinRequestRes,
    ResolveJoinRequestReq,
    ResolveJoinRequestRes,
)
from app.services.neighbourhood_join_service import (
    list_join_requests_handler,
    request_to_join_handler,
    resolve_join_request_handler,
)

router = APIRouter(prefix="/neighbourhood", tags=["neighbourhood"])

@router.post(
    "/join",
    response_model=JoinNeighbourhoodRes,
    status_code=status.HTTP_201_CREATED,
    summary="Request to join a neighbourhood",
)
async def join_neighbourhood(
    body: JoinNeighbourhoodReq,
    db: DbSession,
    claims: dict = Depends(get_current_user),
):
    result = await request_to_join_handler(body.join_code, db, claims)
    return JoinNeighbourhoodRes(status=201, message="Join request submitted", data=result)


@router.get(
    "/join-requests",
    response_model=list[JoinRequestRes],
    summary="List pending join requests for the admin's neighbourhood",
)
async def list_join_requests(
    db: DbSession,
    claims: dict = Depends(get_current_user),
):
    return await list_join_requests_handler(db, claims)

@router.patch(
    "/join-requests/{request_id}",
    response_model=ResolveJoinRequestRes,
    summary="Approve or deny a join request",
)
async def resolve_join_request(
    request_id: UUID,
    body: ResolveJoinRequestReq,
    db: DbSession,
    claims: dict = Depends(get_current_user),
):
    require_role(claims, ["NEIGHBOURHOOD_ADMIN"])
    result = await resolve_join_request_handler(request_id, body.action, db, claims)
    return ResolveJoinRequestRes(status=200, message="Join request updated", data=result)
