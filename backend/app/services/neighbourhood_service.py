from typing import List

from fastapi import HTTPException
from app.core.database import DbSession
from uuid import UUID
from app.schemas.neighbourhood import NeighbourhoodPropertyRes, NeighbourhoodRes, NeighbourhoodMemberRes
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import User
from app.models.audit_log import TargetEntity
from app.models.neighbourhood_user import NeighbourhoodUser, NeighbourhoodRole
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import secrets
import string

from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction

async def create_neighbourhood_handler(name: str, location: str, property_id: UUID, db: DbSession, claims: dict):
    """Creates the neighbourhood
        Makes the user who called the function the neighbourhood admin
        Adds the user's property to the neighbourhood
        Generate the join code """

    if not name or name == "":
        raise HTTPException(400, "No neighbourhood name given.")

    if not location or location == "":
        raise HTTPException(400, "No neighbourhood location given")
    
    if not property_id:
        raise HTTPException(400, "No property id given to link the neighbourhood to")
    
    if not db:
        raise HTTPException(500, "No database session")

    if not claims:
        raise HTTPException(401, "Not authenticated")

    try:
        creator_id = UUID(claims["id"])

        # Get property
        property_obj_result = await db.execute(
            select(Property).where(Property.id == property_id)
        )
        property_obj = property_obj_result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(404, "Property not found")

        if property_obj.neighbourhood_id is not None:
            raise HTTPException(400, "Property is already part of another neighbourhood")

        ownership_result = await db.execute(
            select(PropertyUser).where(
                PropertyUser.property_id == property_id,
                PropertyUser.user_id == creator_id,
            )
        )
        ownership = ownership_result.scalar_one_or_none()

        if not ownership:
            raise HTTPException(403,"You do not own this property")

        creator_result = await db.execute(
            select(User).where(User.id == creator_id)
        )
        creator = creator_result.scalar_one_or_none()

        if not creator:
            raise HTTPException(401, "Authenticated user not found in database")
 
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

        # Add the neighbourhood
        new_neighbourhood = Neighbourhood(
            name=name,
            location=location,
            join_code=join_code,
        )

        db.add(new_neighbourhood)
        # Generate  neighbourhood ID
        await db.flush()

        # Link property
        property_obj.neighbourhood_id = new_neighbourhood.id

        db.add(
            NeighbourhoodUser(
                user_id=creator.id,
                neighbourhood_id=new_neighbourhood.id,
                role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
            )
        )

        # Create single audit entry
        await create_audit_log_item(
            db=db,
            user_id=creator_id,
            action=AuditAction.CREATE,
            target_entity_type=TargetEntity.NEIGHBOURHOOD,
            target_entity_id=new_neighbourhood.id,
            new_values={
                "name": new_neighbourhood.name,
                "location": new_neighbourhood.location,
                "property_id": str(property_obj.id),
                "creator_id": str(creator.id),
            },
        )

        await db.commit()
        await db.refresh(new_neighbourhood)

        return NeighbourhoodRes(
            id=new_neighbourhood.id,
            name=new_neighbourhood.name,
            location=new_neighbourhood.location,
            join_code=new_neighbourhood.join_code,
            created_at=new_neighbourhood.created_at
        )

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            500,
            "Failed to add neighbourhood"
        )

    except HTTPException as he:
        await db.rollback()
        raise he

    except Exception:
        await db.rollback()
        raise HTTPException(500, "Failed to create neighbourhood")


async def get_neighbourhood_properties_service(db: DbSession, claims: dict) -> List[NeighbourhoodPropertyRes]:

    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = UUID(claims["id"])

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(select(Property, Neighbourhood)
                            .outerjoin(Neighbourhood, Neighbourhood.id == Property.neighbourhood_id)
                            .join(PropertyUser, PropertyUser.property_id == Property.id)
                            .where(PropertyUser.user_id == user.id))
    properties = result.all()

    return [
        NeighbourhoodPropertyRes(
            id=property_obj.id,
            address=property_obj.address,
            property_type=property_obj.property_type,
            neighbourhood_id=property_obj.neighbourhood_id,
            neighbourhood_name=(
                neighbourhood.name if neighbourhood else None
            ),
        )
        for property_obj, neighbourhood in properties
    ]
    

async def get_neighbourhood_members_handler(
    neighbourhood_id: UUID, 
    db: DbSession, 
    claims: dict
) -> List[NeighbourhoodMemberRes]:
    
    if not claims:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    current_user_id = UUID(claims["id"])


    neighbourhood_result = await db.execute(
        select(Neighbourhood).where(
            Neighbourhood.id == neighbourhood_id
        )
    )
    neighbourhood = neighbourhood_result.scalar_one_or_none()

    if not neighbourhood:
        raise HTTPException(
            status_code=404,
            detail="Neighbourhood not found"
        )

    admin_result = await db.execute(
        select(NeighbourhoodUser).where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
            NeighbourhoodUser.user_id == current_user_id,
            NeighbourhoodUser.role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
        )
    )
    admin_membership = admin_result.scalar_one_or_none()

    if not admin_membership:
        raise HTTPException(
            status_code=403,
            detail="Only neighbourhood admins can view members"
        )

    members_result = await db.execute(
        select(NeighbourhoodUser, User)
        .join(
            User,
            User.id == NeighbourhoodUser.user_id
        )
        .where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id
        )
        .order_by(
            User.first_name,
            User.last_name
        )
    )

    members = members_result.all()

    return [
        NeighbourhoodMemberRes(
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=membership.role
        )
        for membership, user in members
    ]


async def update_neighbourhood_member_role_handler(
    neighbourhood_id: UUID, 
    member_user_id: UUID, 
    new_role: NeighbourhoodRole, 
    db: DbSession, 
    claims: dict
):
    if not claims:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    current_user_id = UUID(claims["id"])

    try:
        neighbourhood_result = await db.execute(
            select(Neighbourhood).where(
                Neighbourhood.id == neighbourhood_id
            )
        )
        neighbourhood = neighbourhood_result.scalar_one_or_none()

        if not neighbourhood:
            raise HTTPException(
                status_code=404,
                detail="Neighbourhood not found",
            )

        current_admin_result = await db.execute(
            select(NeighbourhoodUser).where(
                NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
                NeighbourhoodUser.user_id == current_user_id,
                NeighbourhoodUser.role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
            )
        )
        current_admin = current_admin_result.scalar_one_or_none()

        if not current_admin:
            raise HTTPException(
                status_code=403,
                detail="Only neighbourhood admins can change member roles"
            )

        member_result = await db.execute(
            select(NeighbourhoodUser).where(
                NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
                NeighbourhoodUser.user_id == member_user_id
            )
        )
        member_membership = member_result.scalar_one_or_none()

        if not member_membership:
            raise HTTPException(
                status_code=404,
                detail="Neighbourhood member not found"
            )

        member_user_result = await db.execute(
            select(User).where(User.id == member_user_id)
        )
        member_user = member_user_result.scalar_one_or_none()

        if not member_user:
            raise HTTPException(
                status_code=404,
                detail="Member user not found"
            )

        old_role = member_membership.role

        if old_role == new_role:
            raise HTTPException(
                status_code=400,
                detail="Member already has this role"
            )

        is_removing_own_admin_role = (
                    current_user_id == member_user_id
                    and old_role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
                    and new_role != NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
                )
        
        if is_removing_own_admin_role:
            other_admin_result = await db.execute(
                select(NeighbourhoodUser).where(
                    NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
                    NeighbourhoodUser.user_id != current_user_id,
                    NeighbourhoodUser.role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
                )
            )
            other_admin = other_admin_result.scalar_one_or_none()

            if not other_admin:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "You must transfer admin rights to another member "
                        "before removing your own admin role"
                    )
                )

        member_membership.role = new_role

        await create_audit_log_item(
            db=db,
            user_id=current_user_id,
            action=AuditAction.UPDATE,
            target_entity_type=TargetEntity.USER,
            target_entity_id=member_user_id,
            old_values={
                "neighbourhood_id": str(neighbourhood_id),
                "role": old_role.value,
            },
            new_values={
                "neighbourhood_id": str(neighbourhood_id),
                "role": new_role.value,
            }
        )

        await db.commit()
        await db.refresh(member_membership)

        return NeighbourhoodMemberRes(
            user_id=member_user.id,
            first_name=member_user.first_name,
            last_name=member_user.last_name,
            email=member_user.email,
            role=member_membership.role,
        )

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update member role"
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update member role",
        )
