from fastapi import HTTPException
from app.core.database import DbSession
from uuid import UUID
from app.schemas.neighbourhood import NeighbourhoodRes
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

async def create_neighbourhood_handler(name: str, loc: str, property_id: UUID, db: DbSession, claims: dict):
    """Creates the neighbourhood
        Makes the user who called the function the neighbourhood admin
        Adds the user's property to the neighbourhood
        Generate the join code """

    if not name or name == "":
        raise HTTPException(400, "No neighbourhood name given.")

    if not loc or loc == "":
        raise HTTPException(400, "No neighbourhood location given")
    
    if not property_id or property_id == "":
        raise HTTPException(400, "No property id given to link the neighbourhood to")
    
    if not claims:
        raise HTTPException(401, "Not authenticated")


    try: 
        #add the neighbourhood   
        newNeighbourhood = Neighbourhood(
            name = name,
            location = loc,
        )

        db.add(newNeighbourhood)
        db.flush()

         #linking prop to neighbourhood 

        #TODO make sure to check that there is a record in the property_users table that links the user and the property
        stmt = select(Property).where(Property.id == property_id)
        property = db.execute(stmt).scalar_one_or_none()

        property.neighbourhood_id = newNeighbourhood.id

        db.flush()
        db.commit()

    except IntegrityError as e:
        db.rollback()
        HTTPException(500, "Failed to add neighbourhood", )
