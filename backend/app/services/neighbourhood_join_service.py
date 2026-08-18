from datetime import datetime, timezone
import secrets
import string
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.neighbourhood_user import NeighbourhoodRole, NeighbourhoodUser
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction, TargetEntity

from app.core.database import DbSession
from app.models.neighbourhood import Neighbourhood
from app.models.neighbourhood_join_request import JoinRequestStatus, NeighbourhoodJoinRequest
from app.models.user import User
from app.schemas.neighbourhood_join import JoinCodeRes, JoinRequestRes, RegenerateJoinCodeRes

async def request_to_join_handler(join_code: str, db: DbSession, claims: dict) -> JoinRequestRes:
    """Requesting to join a neighbourhood"""

    if not db:
        raise HTTPException(500, "No database session")

    if not join_code or join_code.strip() == "":
        raise HTTPException(400, "Join code is required")

    if not claims:
        raise HTTPException(401, "Not authenticated")

    clean_code = join_code.strip()

    try:
        neighbourhood_result = await db.execute(
            select(Neighbourhood)
            .where(Neighbourhood.join_code == clean_code)
        )
        neighbourhood = neighbourhood_result.scalar_one_or_none()

        if not neighbourhood:
            raise HTTPException(404, "Invalid join code")

        user_id = UUID(claims["id"])

        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(401, "User profile not found")


        membership_result = await db.execute(
            select(NeighbourhoodUser).where(
                NeighbourhoodUser.user_id == user.id,
                NeighbourhoodUser.neighbourhood_id == neighbourhood.id,
            )
        )
        existing_membership = membership_result.scalar_one_or_none()

        if existing_membership:
            raise HTTPException(409, "You are already a member of this neighbourhood")

        pending_result = await db.execute(
            select(NeighbourhoodJoinRequest).where(
                NeighbourhoodJoinRequest.neighbourhood_id == neighbourhood.id,
                NeighbourhoodJoinRequest.user_id == user.id,
                NeighbourhoodJoinRequest.status == JoinRequestStatus.PENDING,
            )
        )
        pending = pending_result.scalar_one_or_none()

        if pending:
            raise HTTPException(409, "Already have a pending request")

        join_request = NeighbourhoodJoinRequest(
            neighbourhood_id=neighbourhood.id,
            user_id=user.id,
            status=JoinRequestStatus.PENDING,
        )
        db.add(join_request)

        await db.flush()

        await create_audit_log_item(
            db=db,
            user_id=user.id,
            action=AuditAction.CREATE,
            target_entity_type=TargetEntity.NEIGHBOURHOODJOINREQUEST,
            target_entity_id=join_request.id,
            new_values={
                "user_id": str(user.id),
                "neighbourhood_id": str(join_request.neighbourhood_id),
                "status": join_request.status.value,
            },
        )
        await db.commit()
        await db.refresh(join_request)

        return JoinRequestRes.model_validate(join_request)
    except HTTPException as he:
        await db.rollback()
        raise he
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Pending request already exists for this neighbourhood")


async def get_join_code_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> JoinCodeRes:
    """Retrieve a neighbourhoods join code"""

    if not claims:
        raise HTTPException(401, "Not authenticated")

    try:
        user_id = UUID(claims["id"])
        
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )

        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Authenticated user not found in databse")

        neighbourhood_result = await db.execute(
            select(Neighbourhood)
            .join(NeighbourhoodUser, NeighbourhoodUser.neighbourhood_id == Neighbourhood.id)
            .where(
                Neighbourhood.id == neighbourhood_id,
                NeighbourhoodUser.user_id == user_id,
                NeighbourhoodUser.role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
            )
        )

        neighbourhood = neighbourhood_result.scalar_one_or_none()

        if not neighbourhood:
            raise HTTPException(403, "User is not an administrator this neighbourhood")  

        return JoinCodeRes(
            join_code=neighbourhood.join_code
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            "Failed to get neighbourhood join code"
        )

          

async def regenerate_join_code_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> RegenerateJoinCodeRes:
    """Regenerates a neighbours join code"""

    if not claims:
        raise HTTPException(401, "Not authenticated")

    try:
        user_id = UUID(claims["id"])
        
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )

        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Authenticated user not found in databse")

        neighbourhood_result = await db.execute(
            select(Neighbourhood)
            .join(NeighbourhoodUser, NeighbourhoodUser.neighbourhood_id == Neighbourhood.id)
            .where(
                Neighbourhood.id == neighbourhood_id,
                NeighbourhoodUser.user_id == user_id,
                NeighbourhoodUser.role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
            )
        )

        neighbourhood = neighbourhood_result.scalar_one_or_none()

        if not neighbourhood:
            raise HTTPException(403, "User is not an administrator this neighbourhood")

        # Generate a unique join code
        while True:
            join_code = "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(8)
            )

            stmt_result = await db.execute(select(Neighbourhood).where(
                Neighbourhood.join_code == join_code
            ))

            stmt = stmt_result.scalar_one_or_none()

            if not stmt:
                break

        neighbourhood.join_code = join_code

        await db.commit()
        await db.refresh(neighbourhood)

        return RegenerateJoinCodeRes(
            join_code=neighbourhood.join_code
        )

    except IntegrityError:
            await db.rollback()
            raise HTTPException(500, "Failed to resolve join request")
    except Exception:
        if db:
            await db.rollback()
        raise HTTPException(500, "Failed to resolve join request")

    
async def list_join_requests_handler(neighbourhood_id: UUID, db: DbSession, claims: dict) -> list[JoinRequestRes]:
    """List join requests for a specific neighbourhood as a neighbourhood admin (neighbourhood_id)"""

    if not claims:
        raise HTTPException(401, "Not authenticated")

    admin_id = UUID(claims["id"])

    try:
        admin_membership_result = await db.execute(
            select(NeighbourhoodUser).where(
                NeighbourhoodUser.user_id == admin_id,
                NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
                NeighbourhoodUser.role == "NEIGHBOURHOOD_ADMIN",
            )
        )
        admin_membership = admin_membership_result.scalar_one_or_none()

        if not admin_membership:
            raise HTTPException(
                403,
                "You are not an administrator of this neighbourhood",
            )
        
        requests_result = await db.execute(
            select(NeighbourhoodJoinRequest)
            .where(
                NeighbourhoodJoinRequest.neighbourhood_id == neighbourhood_id
            )
            .order_by(NeighbourhoodJoinRequest.created_at.desc())
        )

        join_requests = requests_result.scalars().all()

        return [
            JoinRequestRes.model_validate(join_request)
            for join_request in join_requests
        ]
    except HTTPException as he:
        raise he
    except IntegrityError:
        raise HTTPException(500, "Failed to list join requests")

async def resolve_join_request_handler(request_id: UUID, property_id: UUID | None, action: str, db: DbSession, claims: dict) -> JoinRequestRes:
    """Accepting or rejecting a users join request to a  neighbourhood"""
    if not request_id:
        raise HTTPException(400, "Join request id is required")
    if not claims:
        raise HTTPException(401, "Not authenticated")

    if action not in ("APPROVE", "DENY"):
        raise HTTPException(400, "Action must be APPROVE or DENY")

    try:
        join_request_result = await db.execute(
            select(NeighbourhoodJoinRequest).where(NeighbourhoodJoinRequest.id == request_id)
        )
        join_request = join_request_result.scalar_one_or_none()
        if not join_request:
            raise HTTPException(404, "Join request not found")

        if join_request.status != "PENDING":
            raise HTTPException(409, "Request has already been resolved")

        admin_id = UUID(claims["id"])

        admin_membership_result = await db.execute(
            select(NeighbourhoodUser).where(
                NeighbourhoodUser.user_id == admin_id,
                NeighbourhoodUser.neighbourhood_id
                == join_request.neighbourhood_id,
                NeighbourhoodUser.role == "NEIGHBOURHOOD_ADMIN",
            )
        )
        admin_membership = admin_membership_result.scalar_one_or_none()

        if not admin_membership:
            raise HTTPException(
                403,
                "You are not an administrator of this neighbourhood",
            )

        old_values = {
            "status": join_request.status,
        }

        if action == "APPROVE":
            if property_id is None:
                raise HTTPException(
                    400,
                    "A property is required when approving a join request",
                )
            
            property_result = await db.execute(
                select(Property)
                .join(
                    PropertyUser,
                    PropertyUser.property_id == Property.id,
                )
                .where(
                    Property.id == property_id,
                    PropertyUser.user_id == join_request.user_id,
                )
            )
            property_obj = property_result.scalar_one_or_none()

            if not property_obj:
                raise HTTPException(
                    403,
                    "The selected property does not belong to the applicant",
                )

            if property_obj.neighbourhood_id is not None:
                raise HTTPException(
                    409,
                    "The selected property already belongs to a neighbourhood",
                )

            property_obj.neighbourhood_id = join_request.neighbourhood_id

            existing_membership_result = await db.execute(
                select(NeighbourhoodUser).where(
                    NeighbourhoodUser.user_id == join_request.user_id,
                    NeighbourhoodUser.neighbourhood_id
                    == join_request.neighbourhood_id,
                )
            )
            existing_membership = (
                existing_membership_result.scalar_one_or_none()
            )

            if not existing_membership:
                db.add(
                    NeighbourhoodUser(
                        user_id=join_request.user_id,
                        neighbourhood_id=join_request.neighbourhood_id,
                        role="RESIDENT",
                    )
                )

            join_request.status = JoinRequestStatus.APPROVED
        else:
            join_request.status = JoinRequestStatus.REJECTED

        join_request.resolved_at = datetime.now(timezone.utc)

        await create_audit_log_item(
            db=db,
            user_id=admin_id,
            action=AuditAction.UPDATE,
            target_entity_type=TargetEntity.NEIGHBOURHOODJOINREQUEST,
            target_entity_id=join_request.id,
            old_values=old_values,
            new_values={
                "user_id": str(join_request.user_id),
                "status": (
                    join_request.status.value
                    if hasattr(join_request.status, "value")
                    else str(join_request.status)
                ),
                "resolved_at": join_request.resolved_at.isoformat(),
                "property_id": str(property_id) if property_id else None,
            },
        )
        await db.commit()
        await db.refresh(join_request)

        return JoinRequestRes.model_validate(join_request)
    except HTTPException as he:
        await db.rollback()
        raise he
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Failed to resolve join request")
    except Exception:
        if db:
            await db.rollback()
        raise HTTPException(500, "Failed to resolve join request")
