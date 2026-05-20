from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.schemas.camera import RegisterCameraReq, CameraRes
from app.models.camera import Camera
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.core.database import DbSession
import re

async def register_camera_handler(req: RegisterCameraReq, db: DbSession, claims: dict) -> CameraRes:
    """ Create the camera and link to property
         add the camera"""
    
    #validation and that
    property_id = req.property_id
    rtsp_url = req.rtsp_url
    visibility = req.visibility
    location = req.location

    if not property_id:
        raise HTTPException(400, "Property ID is missing")
    
    rtsp_url_pattern = r"^rtsp:\/\/(?:([^:\s]+):([^@\s]+)@)?([^\/\s:]+)(?::(\d+))?(\/[^\s]*)?$"

    #check that the camera does not already exist

    if not rtsp_url or rtsp_url == "":
        raise HTTPException(400, "RTSP URL is missing")
    elif not re.search(rtsp_url_pattern, rtsp_url):
        raise HTTPException(400, "RTSP URL is not valid")
    
    if not visibility:
        raise HTTPException(400, "Visibility is missing")
    
    if not location or location == "":
        raise HTTPException(400, "Location is missing")
    
    if not db:
        raise HTTPException(500, "No database session")

    if not claims:
        raise HTTPException(401, "Not authenticated")

    try:
        #get neighbourhood
        stmt = select(Property).where(Property.id == property_id)
        property = db.execute(stmt).scalar_one_or_none()

        if not property:
            raise HTTPException(403, "Property does not exist")
        
        stmt = select(PropertyUser).where(PropertyUser.property_id == property_id)
        prop_user = db.execute(stmt).scalar_one_or_none()

        if not prop_user:
            raise HTTPException(403, "User does not have access to this property")

        if (prop_user.user.cognito_sub != claims['sub']):
            raise HTTPException(403, "This user does not live in the property they are trying to add to the neighbourhood they are creating")

        neighbourhood_id = property.neighbourhood_id

        new_camera = Camera(
            property_id = property_id,
            neighbourhood_id = neighbourhood_id,
            rtsp_url = rtsp_url,
            visibility = visibility,
            location = location,
        )

        db.add(new_camera)
        db.flush()
        db.refresh(new_camera)

        db.commit()

        return CameraRes(
            id = new_camera.id,
            property_id=new_camera.property_id,
            neighbourhood_id=new_camera.neighbourhood_id,
            rtsp_url=new_camera.rtsp_url,
            visibility=new_camera.visibility,
            location=new_camera.location,
            created_at=new_camera.created_at
        )

    except IntegrityError as ie:
        db.rollback()
        raise HTTPException(500, "Could not register camera")
    except HTTPException as he:
        db.rollback()
        raise he