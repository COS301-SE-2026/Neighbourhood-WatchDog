from fastapi import HTTPException
from app.core.database import DbSession
from uuid import UUID
from app.schemas.neighbourhood import NeighbourhoodRes, CreateNeighbourhoodRes
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property
from app.models.user import User
from app.models.property_user import PropertyUser
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import random

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
        #add the neighbourhood   
        new_neighbourhood = Neighbourhood(
            name = name,
            location = location,
        )

        db.add(new_neighbourhood)
        db.flush()
        db.refresh(new_neighbourhood)

         #linking prop to neighbourhood 1
        stmt = select(Property).where(Property.id == property_id)
        property = db.execute(stmt).scalar_one_or_none()

        if not property:
            raise HTTPException(404, "Property not found")

        stmt = select(PropertyUser).where(PropertyUser.property_id == property_id)
        prop_user = db.execute(stmt).scalar_one_or_none()

        if not prop_user:
            raise HTTPException(403, "User does not have access to this property")

        if (prop_user.user.cognito_sub != claims['sub']):
            raise HTTPException(403, "This user does not live in the property they are trying to add to the neighbourhood they are creating")
        
        property.neighbourhood_id = new_neighbourhood.id

        db.flush()
        db.commit()

        #TODO add the join code stuff when ange is done with the join neighbourhood part

        return NeighbourhoodRes(
            id = new_neighbourhood.id,
            name = new_neighbourhood.name,
            location = new_neighbourhood.location,
            join_code = "neighbourhood1",
            created_at = new_neighbourhood.created_at
        )

    except IntegrityError as e:
        db.rollback()
        HTTPException(500, "Failed to add neighbourhood")
    except HTTPException as he:
        db.rollback()
        raise he
