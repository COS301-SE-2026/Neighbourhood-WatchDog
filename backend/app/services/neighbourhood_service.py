from typing import List

from fastapi import HTTPException
from app.core.database import DbSession
from uuid import UUID
from app.schemas.neighbourhood import NeighbourhoodPropertyRes, NeighbourhoodRes
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import User, UserRole
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
        raise HTTPException(400, "No neighbourhood locationation given")
    
    if not property_id:
        raise HTTPException(400, "No property id given to link the neighbourhood to")
    
    if not db:
        raise HTTPException(500, "No database session")

    if not claims:
        raise HTTPException(401, "Not authenticated")

    try:
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

        # Get property
        property_obj_result = await db.execute(
            select(Property).where(Property.id == property_id)
        )
        property_obj = property_obj_result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(404, "Property not found")

        if property_obj.neighbourhood_id is not None:
            raise HTTPException(
                400,
                "Property is already part of another neighbourhood"
            )

        # Verify user owns property
        prop_user_result = await db.execute(
            select(PropertyUser).where(
                PropertyUser.property_id == property_id
            )
        )

        prop_user = prop_user_result.scalar_one_or_none()

        if not prop_user:
            raise HTTPException(
                403,
                "User does not have access to this property"
            )

        if prop_user.user.cognito_sub != claims["sub"]:
            raise HTTPException(
                403,
                "User does not live in the property they are trying to link"
            )

        # Link property
        property_obj.neighbourhood_id = new_neighbourhood.id

        # Promote creator
        creator_result = await db.execute(
            select(User).where(
                User.cognito_sub == claims["sub"]
            )
        )

        creator = creator_result.scalar_one_or_none()

        if not creator:
            raise HTTPException(
                401,
                "Authenticated user not found in database"
            )

        creator.role = UserRole.NEIGHBOURHOOD_ADMIN

        # Create single audit entry
        create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.CREATE,
            target_entity_type="Neighbourhood",
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


async def get_neighbourhood_properties_service(db: DbSession, claims: dict) -> List[NeighbourhoodPropertyRes]:

    user_result = await db.execute(select(User).where(User.id == UUID(claims["id"])))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(select(Property, Neighbourhood)
                            .outerjoin(Neighbourhood, Neighbourhood.id == Property.neighbourhood_id)
                            .join(PropertyUser, PropertyUser.property_id == Property.id)
                            .where(PropertyUser.user_id == user.id))
    results_all = result.all()

    if not result:
        raise HTTPException(status_code=404, detail="No properties found for this user")

    return [
        NeighbourhoodPropertyRes(
            id=property.id,
            address=property.address,
            property_type=property.property_type,
            neighbourhood_id=property.neighbourhood_id,
            neighbourhood_name=neighbourhood.name if neighbourhood else None,
        )
        for property, neighbourhood in results_all
    ]

    
