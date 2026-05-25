from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import DbSession
from app.models.neighbourhood import Neighbourhood
from app.models.neighbourhood_join_request import NeighbourhoodJoinRequest
from app.models.user import User
from app.schemas.neighbourhood_join import JoinRequestRes

async def request_to_join_handler(join_code: str, db: DbSession, claims: dict) -> JoinRequestRes:
    if not join_code or join_code.strip() == "":
        raise HTTPException(400, "Join code is required")
    if not db:
        raise HTTPException(500, "No database session")
    if not claims:
        raise HTTPException(401, "Not authenticated")

    clean_code = join_code.strip()

    try:
        neighbourhood = db.execute(
            select(Neighbourhood).where(Neighbourhood.join_code == clean_code)
        ).scalar_one_or_none()
        if not neighbourhood:
            raise HTTPException(404, "Invalid join code")

        user_email = claims.get("email")
        user_sub = claims.get("sub")

        user = None
        if user_email:
            user = db.execute(select(User).where(User.email == user_email)).scalar_one_or_none()
        if not user and user_sub:
            user = db.execute(select(User).where(User.cognito_sub == user_sub)).scalar_one_or_none()
        if not user:
            raise HTTPException(401, "Not authenticated")

        pending = db.execute(
            select(NeighbourhoodJoinRequest).where(
                NeighbourhoodJoinRequest.neighbourhood_id == neighbourhood.id,
                NeighbourhoodJoinRequest.user_id == user.id,
                NeighbourhoodJoinRequest.status == "PENDING",
            )
        ).scalar_one_or_none()
        if pending:
            raise HTTPException(409, "Already have a pending request")

        join_request = NeighbourhoodJoinRequest(
            neighbourhood_id=neighbourhood.id,
            user_id=user.id,
            status="PENDING",
        )
        db.add(join_request)
        db.flush()
        db.commit()
        return JoinRequestRes.model_validate(join_request)
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to create join request")


async def list_join_requests_handler(db: DbSession, claims: dict) -> list[JoinRequestRes]:
    if not db:
        raise HTTPException(500, "No database session")
    if not claims:
        raise HTTPException(401, "Not authenticated")

    if claims.get("custom:role") != "NEIGHBOURHOOD_ADMIN":
        raise HTTPException(403, "Insufficient permissions")

    neighbourhood_id = claims.get("custom:neighbourhood_id")
    if not neighbourhood_id:
        raise HTTPException(403, "Neighbourhood context missing")

    try:
        neighbourhood_uuid = UUID(str(neighbourhood_id))
        requests = db.execute(
            select(NeighbourhoodJoinRequest)
            .where(NeighbourhoodJoinRequest.neighbourhood_id == neighbourhood_uuid)
            .order_by(NeighbourhoodJoinRequest.created_at.desc())
        ).scalars().all()
        return [JoinRequestRes.model_validate(request) for request in requests]
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to list join requests")

async def resolve_join_request_handler(request_id, action: str, db: DbSession, claims: dict) -> JoinRequestRes:
    if not request_id:
        raise HTTPException(400, "Join request id is required")
    if not db:
        raise HTTPException(500, "No database session")
    if not claims:
        raise HTTPException(401, "Not authenticated")

    if action not in ("APPROVE", "DENY"):
        raise HTTPException(400, "Action must be APPROVE or DENY")

    try:
        join_request = db.execute(
            select(NeighbourhoodJoinRequest).where(NeighbourhoodJoinRequest.id == request_id)
        ).scalar_one_or_none()
        if not join_request:
            raise HTTPException(404, "Join request not found")

        if claims.get("custom:role") != "NEIGHBOURHOOD_ADMIN":
            raise HTTPException(403, "Insufficient permissions")

        if join_request.status != "PENDING":
            raise HTTPException(409, "Request has already been resolved")

        user = db.execute(
            select(User).where(User.id == join_request.user_id)
        ).scalar_one_or_none()
        if not user:
            raise HTTPException(404, "User not found")

        if action == "APPROVE":
            user.role = "RESIDENT"
            user.neighbourhood_id = join_request.neighbourhood_id
            join_request.status = "APPROVED"
        else:
            join_request.status = "DENIED"

        join_request.resolved_at = datetime.now(timezone.utc)
        db.commit()
        return JoinRequestRes.model_validate(join_request)
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to resolve join request")
