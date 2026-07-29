from fastapi import HTTPException
from app.core.database import DbSession
from uuid import UUID
from app.schemas.neighbourhood import NeighbourhoodRes
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

            stmt = select(Neighbourhood).where(
                Neighbourhood.join_code == join_code
            )

            if not db.execute(stmt).scalar_one_or_none():
                break

        # Add the neighbourhood
        new_neighbourhood = Neighbourhood(
            name=name,
            location=location,
            join_code=join_code,
        )

        db.add(new_neighbourhood)
        # Generate  neighbourhood ID
        db.flush()

        # Get property
        property_obj = db.execute(
            select(Property).where(Property.id == property_id)
        ).scalar_one_or_none()

        if not property_obj:
            raise HTTPException(404, "Property not found")

        if property_obj.neighbourhood_id is not None:
            raise HTTPException(
                400,
                "Property is already part of another neighbourhood"
            )

        # Verify user owns property
        prop_user = db.execute(
            select(PropertyUser).where(
                PropertyUser.property_id == property_id
            )
        ).scalar_one_or_none()

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
        creator = db.execute(
            select(User).where(
                User.cognito_sub == claims["sub"]
            )
        ).scalar_one_or_none()

        if not creator:
            raise HTTPException(
                401,
                "Authenticated user not found in database"
            )

        creator.role = UserRole.NEIGHBOURHOOD_ADMIN
        creator.neighbourhood_id = new_neighbourhood.id

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

        db.commit()
        db.refresh(new_neighbourhood)

        return NeighbourhoodRes(
            id=new_neighbourhood.id,
            name=new_neighbourhood.name,
            location=new_neighbourhood.location,
            join_code=new_neighbourhood.join_code,
            created_at=new_neighbourhood.created_at
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            500,
            "Failed to add neighbourhood"
        )

    except HTTPException as he:
        db.rollback()
        raise he