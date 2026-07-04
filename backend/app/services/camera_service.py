from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.schemas.camera import RegisterCameraReq, CameraRes, CamerasRes, CameraEditReq
from app.models.camera import Camera
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import User
from app.core.database import DbSession
from uuid import UUID

NO_DB_SESSION = "No database session"
NOT_AUTHENTICATED = "Not authenticated"

async def register_camera_handler(req: RegisterCameraReq, db: DbSession, claims: dict) -> CameraRes:
    if not db:
        raise HTTPException(500, NO_DB_SESSION)
    if not claims:
        raise HTTPException(401, NOT_AUTHENTICATED)

    try:
        stmt = select(Property).where(Property.id == req.property_id)
        property_obj = db.execute(stmt).scalar_one_or_none()

        if not property_obj:
            raise HTTPException(404, "Property not found")

        new_camera = Camera(
            property_id=req.property_id,
            neighbourhood_id=property_obj.neighbourhood_id,
            rtsp_url=req.rtsp_url,
            visibility=req.visibility,
            location=req.location,
        )
        db.add(new_camera)
        db.commit()

        return CameraRes(
            id=new_camera.id,
            property_id=new_camera.property_id,
            neighbourhood_id=new_camera.neighbourhood_id,
            rtsp_url=new_camera.rtsp_url,
            visibility=new_camera.visibility,
            location=new_camera.location,
            created_at=new_camera.created_at,
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Could not register camera")
    except HTTPException as he:
        db.rollback()
        raise he

def deregister_camera_handler(camera_id: UUID, db: Optional[DbSession], claims: Optional[dict]):
    if not db:
        raise HTTPException(status_code=500, detail=NO_DB_SESSION)
    if not claims:
        raise HTTPException(status_code=500, detail=NOT_AUTHENTICATED)
    
    try:
        stmt = select(Camera).where(Camera.id == camera_id)
        camera_obj = db.execute(stmt).scalar_one_or_none()

        if not camera_obj:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        prop_user = db.execute(
            select(PropertyUser).where(PropertyUser.property_id == camera_obj.property_id)
            ).scalar_one_or_none()
        
        if not prop_user or prop_user.user.cognito_sub != claims.get("sub"):
            raise HTTPException(status_code=403, detail="Forbidden")

        
        db.execute(delete(Camera).where(Camera.id == camera_id))
        db.commit()
        
    except HTTPException as he:
        db.rollback()
        raise he
    
def edit_camera_handler(
    camera_id: UUID, 
    req: CameraEditReq,
    db: Session, 
    claims: dict
    ):
    
    try:

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided to update")
    
        stmt = select(Camera).where(Camera.id == camera_id)
        camera_obj = db.execute(stmt).scalar_one_or_none()

        if not camera_obj:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        prop_user = db.execute(
            select(PropertyUser)
            .join(PropertyUser.user)
            .where(
                PropertyUser.property_id == camera_obj.property_id,
                User.cognito_sub == claims.get("sub")
                
                )
            ).scalar_one_or_none()
        
        if not prop_user:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        for field, value in update_data.items():
            setattr(camera_obj, field, value)

        db.commit()
        db.refresh(camera_obj)

        return camera_obj
    
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update camera")



async def list_cameras_handler(property_id: str, db: DbSession, claims: dict) -> CamerasRes:
    if not db:
        raise HTTPException(500, NO_DB_SESSION)

    if not claims:
        raise HTTPException(401, NOT_AUTHENTICATED)

    try:
        prop_uuid = UUID(property_id)
    except ValueError:
        raise HTTPException(400, "Invalid property ID")

    stmt = select(Property).where(Property.id == prop_uuid)
    property_obj = db.execute(stmt).scalar_one_or_none()

    if not property_obj:
        raise HTTPException(403, "Property does not exist")

    stmt = select(PropertyUser).where(PropertyUser.property_id == prop_uuid)
    prop_user = db.execute(stmt).scalar_one_or_none()

    if not prop_user:
        raise HTTPException(403, "User does not have access to this property")

    if prop_user.user.cognito_sub != claims["sub"]:
        raise HTTPException(403, "This user does not have access to this property")

    stmt = select(Camera).where(Camera.property_id == prop_uuid).order_by(Camera.created_at.desc())
    cameras = db.execute(stmt).scalars().all()

    return CamerasRes(
        status=200,
        message="Cameras fetched successfully",
        data=[
            CameraRes(
                id=c.id,
                property_id=c.property_id,
                neighbourhood_id=c.neighbourhood_id,
                rtsp_url=c.rtsp_url,
                visibility=c.visibility,
                location=c.location,
                created_at=c.created_at,
            )
            for c in cameras
        ],
    )
