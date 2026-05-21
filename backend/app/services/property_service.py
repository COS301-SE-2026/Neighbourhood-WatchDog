from fastapi import HTTPException
from app.core.database import DbSession
from sqlalchemy import select
from app.models.user import User
from app.models.property import Property, PropertyTypeEnum
from app.models.property_user import PropertyUser
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List

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