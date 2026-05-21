from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.schemas.camera import RegisterCameraReq, CameraRes, CamerasRes
from app.models.camera import Camera
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.core.database import DbSession
from uuid import UUID
import re

async def register_camera_handler(req: RegisterCameraReq, db: DbSession, claims: dict) -> CameraRes:
    ...
    return CameraRes(
        id=new_camera.id,
        property_id=new_camera.property_id,
        neighbourhood_id=new_camera.neighbourhood_id,
        rtsp_url=new_camera.rtsp_url,
        visibility=new_camera.visibility,
        location=new_camera.location,
        created_at=new_camera.created_at
    )

async def list_cameras_handler(property_id: str, db: DbSession, claims: dict) -> CamerasRes:
    if not db:
        raise HTTPException(500, "No database session")

    if not claims:
        raise HTTPException(401, "Not authenticated")

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