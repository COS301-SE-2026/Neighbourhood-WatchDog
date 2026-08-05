from app.schemas.camera import RegisterCameraReq, CameraRes, CameraListItemRes, CamerasRes, CameraEditReq
from app.models.camera import Camera
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import User
from app.services.rtsp_encryption import encrypt_rtsp_url, decrypt_rtsp_url

from app.services.audit_service import create_audit_log_item

from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.audit_log import AuditAction, TargetEntity

import logging

logger = logging.getLogger(__name__)

NO_DB_SESSION = "No database session"
NOT_AUTHENTICATED = "Not authenticated"

async def register_camera_handler(req: RegisterCameraReq, db: AsyncSession, claims: dict) -> CameraRes:
    if not db:
        raise HTTPException(500, NO_DB_SESSION)
    if not claims:
        raise HTTPException(401, NOT_AUTHENTICATED)

    try:
        result = await db.execute(select(Property).where(Property.id == req.property_id))
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(404, "Property not found")

        # encrypting the rtsp url
        plaintext_rtsp_url = req.rtsp_url
        ciphertext_rtsp_url = encrypt_rtsp_url(plaintext_rtsp_url)

        new_camera = Camera(
            property_id=req.property_id,
            name=req.name,
            neighbourhood_id=property_obj.neighbourhood_id,
            rtsp_url=ciphertext_rtsp_url,
            visibility=req.visibility,
            location=req.location,
        )
        db.add(new_camera)

        # Get ID before commit
        await db.flush()

        create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.CREATE,
            target_entity_type=TargetEntity.CAMERA,
            target_entity_id=new_camera.id,
            new_values={
                "property_id": str(new_camera.property_id),
                "name": new_camera.name,
                "neighbourhood_id": str(new_camera.neighbourhood_id),
                "visibility": new_camera.visibility,
                "location": new_camera.location,
            },
        )

        await db.commit()
        await db.refresh(new_camera)

        return CameraRes(
            id=new_camera.id,
            name=new_camera.name,
            property_id=new_camera.property_id,
            neighbourhood_id=new_camera.neighbourhood_id,
            rtsp_url=new_camera.rtsp_url,
            visibility=new_camera.visibility,
            location=new_camera.location,
            enabled=new_camera.enabled,
            created_at=new_camera.created_at,
        )

    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Could not register camera")
    except HTTPException as he:
        await db.rollback()
        raise he

async def deregister_camera_handler(camera_id: UUID, db: Optional[AsyncSession], claims: Optional[dict]):
    if not db:
        raise HTTPException(status_code=500, detail=NO_DB_SESSION)
    if not claims:
        raise HTTPException(status_code=500, detail=NOT_AUTHENTICATED)
    
    try:
        result = await db.execute(select(Camera).where(Camera.id == camera_id))
        camera_obj = result.scalar_one_or_none()

        if not camera_obj:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        prop_user_result = await db.execute(
            select(PropertyUser)
            .options(joinedload(PropertyUser.user))
            .where(PropertyUser.property_id == camera_obj.property_id)
        )
        prop_user = prop_user_result.scalar_one_or_none()

        if not prop_user or prop_user.user.cognito_sub != claims.get("sub"):
            raise HTTPException(status_code=403, detail="Forbidden")

        
        old_values = {
            "property_id": str(camera_obj.property_id),
            "name": camera_obj.name,
            "neighbourhood_id": str(camera_obj.neighbourhood_id),
            "visibility": camera_obj.visibility,
            "location": camera_obj.location,
        }

        await db.delete(camera_obj)

        create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.DELETE,
            target_entity_type=TargetEntity.CAMERA,
            target_entity_id=camera_obj.id,
            old_values=old_values,
        )

        await db.commit()
        
    except HTTPException as he:
        await db.rollback()
        raise he
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Could not deregister camera")
    except Exception:
        await db.rollback()
        raise HTTPException(500, "Failed to delete camera")
    
async def edit_camera_handler(
    camera_id: UUID, 
    req: CameraEditReq,
    db: AsyncSession, 
    claims: dict
    ) -> CameraRes:
    
    try:

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided to update")
    
        result = await db.execute(select(Camera).where(Camera.id == camera_id))
        camera_obj = result.scalar_one_or_none()

        if not camera_obj:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        prop_user_result = await db.execute(
            select(PropertyUser)
            .join(PropertyUser.user)
            .where(
                PropertyUser.property_id == camera_obj.property_id,
                User.cognito_sub == claims.get("sub")
                
                )
            )
        prop_user = prop_user_result.scalar_one_or_none()
        
        if not prop_user:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        old_values = {
            field: getattr(camera_obj, field)
            for field in update_data.keys()
        }


        for field, value in update_data.items():
            setattr(camera_obj, field, value)


        new_values = {
            field: getattr(camera_obj, field)
            for field in update_data.keys()
        }


        create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.UPDATE,
            target_entity_type=TargetEntity.CAMERA,
            target_entity_id=camera_obj.id,
            old_values=old_values,
            new_values=new_values,
        )


        await db.commit()
        await db.refresh(camera_obj)

        return CameraRes(
            id=camera_obj.id,
            name=camera_obj.name,
            property_id=camera_obj.property_id,
            neighbourhood_id=camera_obj.neighbourhood_id,
            rtsp_url=camera_obj.rtsp_url,
            visibility=camera_obj.visibility,
            location=camera_obj.location,
            enabled=camera_obj.enabled,
            created_at=camera_obj.created_at,
        )
    
    except HTTPException as he:
        await db.rollback()
        raise he
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update camera")



async def list_cameras_handler(property_id: str, db: AsyncSession, claims: dict) -> CamerasRes:
    if not db:
        raise HTTPException(500, NO_DB_SESSION)

    if not claims:
        raise HTTPException(401, NOT_AUTHENTICATED)

    try:
        prop_uuid = UUID(property_id)
    except ValueError:
        raise HTTPException(400, "Invalid property ID")

    stmt = select(Property).where(Property.id == prop_uuid)
    result = await db.execute(stmt)
    property_obj = result.scalar_one_or_none()

    if not property_obj:
        raise HTTPException(403, "Property does not exist")

    prop_user_result = await db.execute(
        select(PropertyUser)
        .options(joinedload(PropertyUser.user))
        .where(PropertyUser.property_id == prop_uuid)
    )
    prop_user = prop_user_result.scalar_one_or_none()

    if not prop_user or prop_user.user.cognito_sub != claims.get("sub"):
        raise HTTPException(
            status_code=403,
            detail="This user does not have access to this property",
        )

    stmt = select(Camera).where(Camera.property_id == prop_uuid).order_by(Camera.created_at.desc())
    result = await db.execute(stmt)
    cameras = result.scalars().all()

    return CamerasRes(
        status=200,
        message="Cameras fetched successfully",
        data=[
            CameraListItemRes(
                id=c.id,
                name=c.name,
                property_id=c.property_id,
                neighbourhood_id=c.neighbourhood_id,
                rtsp_url=decrypt_rtsp_url(c.rtsp_url),
                visibility=c.visibility,
                location=c.location,
                enabled=c.enabled,
                created_at=c.created_at,
            )
            for c in cameras
        ],
    )
