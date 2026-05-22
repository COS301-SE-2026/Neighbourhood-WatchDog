from fastapi import HTTPException
from app.core.database import DbSession
from sqlalchemy import select
from app.models.user import User
from app.models.property import Property, PropertyTypeEnum
from app.models.property_user import PropertyUser
from app.models.camera import Camera
from app.models.neighbourhood import Neighbourhood
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import UUID

async def create_property_handler(addr: str, prop_type: PropertyTypeEnum, claims: dict, db: DbSession) -> Property:
    
    if not addr or addr == "":
        raise HTTPException(400, "No address or empty address field.")

    if not prop_type:
        raise HTTPException(400, "No property type given")
    
    if not claims:
        raise HTTPException(401, "Not authenticated")

    new_property = Property(
        address = addr,
        property_type = prop_type
    )

    #TODO deal with cases where the property type is public (for now it does not really matter what it is)
    try:
        # get user
        stmt = select(User).where(User.cognito_sub == claims['sub'])
        user = db.execute(stmt).scalar_one_or_none()

        # add prop
        db.add(new_property)
        db.flush()

        #set user to prop admin
        new_property_user = PropertyUser(
            user_id = user.id,
            property_id = new_property.id,
            is_admin = True
        )
        db.add(new_property_user)
        db.flush()
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to add to property database")

    return new_property


async def get_user_properties_handler(claims: dict, db: DbSession) -> List[Property]:
    """Fetch all properties owned by the current user"""

    if not claims:
        raise HTTPException(401, "Not authenticated")

    try:
        #get user by cognito_sub
        stmt = select(User).where(User.cognito_sub == claims['sub'])
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            raise HTTPException(404, "User not found")

        #get all properties for this user
        stmt = select(Property).join(PropertyUser).where(PropertyUser.user_id == user.id)
        properties = db.execute(stmt).scalars().all()

        return properties

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch properties: {str(e)}")
    
async def get_property_details_handler(property_id: UUID, db: DbSession):
    """gets all the details for the property page"""

    if not property_id:
        raise HTTPException(400, "No property ID provided")

    try:
        #get property
        stmt = select(Property).where(Property.id == property_id)
        property = db.execute(stmt).scalar_one_or_none()

        if not property:
            raise HTTPException(404, "Property not found")
        
        stmt = select(PropertyUser).where(PropertyUser.property_id == property_id)
        propuse = db.execute(stmt).scalars().all()

        users = [
            {
                "id": pu.user.id,
                "email": pu.user.email,
                "first_name": pu.user.first_name,
                "last_name": pu.user.last_name,
            }
            for pu in propuse
        ]

        # get neighbourhood if property is linked to one
        neighbourhood = None
        if property.neighbourhood_id:
            stmt = select(Neighbourhood).where(Neighbourhood.id == property.neighbourhood_id)
            neighbourhood_obj = db.execute(stmt).scalar_one_or_none()
            if neighbourhood_obj:
                neighbourhood = {
                    "id": neighbourhood_obj.id,
                    "name": neighbourhood_obj.name,
                    "location": neighbourhood_obj.location,
                    "join_code": neighbourhood_obj.join_code,
                    "created_at": neighbourhood_obj.created_at,
                }

        # get cameras linked to this property
        stmt = select(Camera).where(Camera.property_id == property_id)
        cameras = db.execute(stmt).scalars().all()
        camera_list = [
            {
                "id": cam.id,
                "location": cam.location,
                "visibility": cam.visibility.value,
                "created_at": cam.created_at,
            }
            for cam in cameras
        ]

        return {
            "property_id": property.id,
            "address": property.address,
            "property_type": property.property_type.value,
            "created_at": property.created_at,
            "users": users,
            "neighbourhood": neighbourhood,
            "cameras": camera_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch property details: {str(e)}")