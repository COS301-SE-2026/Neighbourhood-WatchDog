import logging
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.auth.authorization import is_property_member
from app.core.database import DbSession
from app.models.audit_log import AuditAction, TargetEntity
from app.models.camera import Camera
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property, PropertyTypeEnum
from app.models.property_user import PropertyUser
from app.models.user import User
from app.services.audit_service import create_audit_log_item

logger = logging.getLogger(__name__)

async def create_property_handler(
    addr: str, 
    prop_type: PropertyTypeEnum, 
    claims: dict, 
    db: DbSession, 
    latitude: float | None = None,
    longitude: float | None = None
) -> Property:
    """Creates a new property. Takes in the address, property type (PUBLIC or PRIVATE), 
    claims and the DbSession, creates the property and returns the created property"""

    if not addr or addr == "":
        logger.warning("create_property called with empty address, claims=%s", claims)
        raise HTTPException(400, "No address or empty address field.")

    if not prop_type:
        logger.warning("create_property called with no property type, claims=%s", claims)
        raise HTTPException(400, "No property type given")
    
    if not claims:
        logger.warning("create_property called with no claims")
        raise HTTPException(401, "Not authenticated")

    new_property = Property(
        address = addr,
        latitude = latitude,
        longitude = longitude, 
        property_type = prop_type
    )

    #TODO deal with cases where the property type is public (for now it does not really matter what it is)
    try:
        # get user
        stmt = select(User).where(User.cognito_sub == claims['sub'])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("create_property: no user found for cognito_sub=%s", claims['sub'])
            raise HTTPException(404, "User not found")

        # add prop
        db.add(new_property)
        await db.flush()

        #set user to prop admin
        new_property_user = PropertyUser(
            user_id = user.id,
            property_id = new_property.id,
            is_admin = True
        )
        db.add(new_property_user)
        await db.flush()

        await create_audit_log_item(
            db=db,
            user_id=user.id,
            action=AuditAction.CREATE,
            target_entity_type=TargetEntity.PROPERTY,
            target_entity_id=new_property.id,
            new_values={
                "address": new_property.address,
                "property_type": new_property.property_type.value, 
                "latitude": new_property.latitude, 
                "longitude": new_property.longitude
            },
        )

        await db.commit()
        logger.info("Property created: id=%s address=%s user_id=%s", new_property.id, addr, user.id)
        return new_property
    
    except IntegrityError:
        await db.rollback()
        logger.error("IntegrityError creating property for user claims=%s", claims)
        raise HTTPException(500, "Failed to add to property database")
    except HTTPException as he:
        await db.rollback()
        raise he


async def get_user_properties_handler(
    claims: dict,
    db: DbSession
) -> List[Property]:
    """Fetch all properties owned by the current user"""

    if not claims:
        logger.warning("get_user_properties: no claims found for request for user properties")
        raise HTTPException(401, "Not authenticated")

    try:
        #get user by cognito_sub
        stmt = select(User).where(User.cognito_sub == claims['sub'])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("get_user_properties: no user found for cognito_sub=%s", claims['sub'])
            raise HTTPException(404, "User not found")

        #get all properties for this user
        stmt = select(Property).join(PropertyUser).where(PropertyUser.user_id == user.id)
        result = await db.execute(stmt)
        properties = result.scalars().all()

        logger.info("get_user_properties: properties retrieved successfully for user_id=%s", user.id)
        return properties

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch properties: {str(e)}")
    
async def get_property_details_handler(property_id: UUID, db: DbSession, claims: dict) -> dict:

    """Gets all the details for the property page"""
    allowed = claims.get("custom:role") == "SYSTEM_ADMIN" or await is_property_member(property_id, claims, db)
    if not allowed:
        raise HTTPException(403, "You do not have permission to view this property.")

    if not property_id:
        logger.warning("get_property_details: no property id provided")
        raise HTTPException(400, "No property ID provided.")

    try:
        #get property
        stmt = select(Property).where(Property.id == property_id)
        result = await db.execute(stmt)
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            logger.warning("get_property_details: could not find the property with the property_id=%s", property_id)
            raise HTTPException(404, "Property not found.")

        # Getting the users through the property_user table
        stmt = (
            select(PropertyUser)
            .where(PropertyUser.property_id == property_id)
            .options(selectinload(PropertyUser.user))
        )
        result = await db.execute(stmt)
        property_users = result.scalars().all()
        
        users = [
            {
                "id": pu.user.id,
                "email": pu.user.email,
                "first_name": pu.user.first_name,
                "last_name": pu.user.last_name,
            }
            for pu in property_users
        ]

        # get neighbourhood if property is linked to one
        neighbourhood = None
        if property_obj.neighbourhood_id:
            stmt = select(Neighbourhood).where(Neighbourhood.id == property_obj.neighbourhood_id)
            result = await db.execute(stmt)
            neighbourhood_obj = result.scalar_one_or_none()
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
        result = await db.execute(stmt)
        cameras = result.scalars().all()
        camera_list = [
            {
                "id": cam.id,
                "location": cam.location,
                "visibility": cam.visibility.value,
                "created_at": cam.created_at,
            }
            for cam in cameras
        ]

        logger.info("get_property_details: details retrieved successfully for proeprty_id=%s.", property_obj.id)
        return {
            "property_id": property_obj.id,
            "address": property_obj.address,
            "property_type": property_obj.property_type.value, 
            "latitude": property_obj.latitude, 
            "longitude": property_obj.longitude, 
            "created_at": property_obj.created_at,
            "users": users,
            "neighbourhood": neighbourhood,
            "cameras": camera_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_property_details: exception raised.")
        raise HTTPException(500, f"Failed to fetch property details: {str(e)}")