from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.schemas.camera import RegisterCameraReq, CameraRes
from app.models.camera import Camera
from app.models.property import Property
from app.core.database import DbSession

async def register_camera_handler(req: RegisterCameraReq, db: DbSession, claims: dict) -> CameraRes:
    """ Create the camera and link to property
         add the camera"""
    
    try:
        property_id = req.property_id
        rtsp_url = req.rtsp_url
        visibility = req.visibility
        location = req.location
        
        #get neighbourhood
        stmt = select(Property).where(Property.id == property_id)
        property = db.execute(stmt).scalar_one_or_none

        if not property:
            raise HTTPException(403, "Property does not exist")

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

        db.commit()

    except IntegrityError as ie:
        db.rollback()
        raise HTTPException(500, "Could not register camera")
    except HTTPException as he:
        db.rollback()
        raise he