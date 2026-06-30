from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.auth.rbac import require_role
from app.core.database import DbSession

from app.schemas.camera_settings import (
    CameraSettingsResponse, 
    CreateZoneRequest,
    UpdateCameraSettingsRequest,
    ZoneResponse
)

from app.services.camera_settings_service import (
    create_zone_handler, 
    delete_zone_handler, 
    get_camera_settings_handler, 
    update_camera_settings_handler

)


router = APIRouter(prefix="/cameras", tags=["camera-settings"])


ZONE_EDITOR_ROLES = ["NEIGHBOURHOOD_ADMIN", "PROP_ADMIN", "SYSTEM_ADMIN"]


@router.get("/{camera_id}/settings", response_model=CameraSettingsResponse)
async def get_settings(

    camera_id: UUID,
    claims: dict = Depends(get_current_user),
    db: DbSession = None

):
    
    """Getting the confidence threshold and detection zones for a camera"""

    require_role(claims, ZONE_EDITOR_ROLES)
    
    return await get_camera_settings_handler(camera_id, db)


@router.patch("/{camera_id}/settings")
async def update_settings(

    camera_id: UUID,
    payload: UpdateCameraSettingsRequest,
    claims: dict = Depends(get_current_user),
    db: DbSession = None

):
    
    """Updating the confidence threshold for a camera"""
    
    require_role(claims, ZONE_EDITOR_ROLES)

    if payload.confidence_threshold is None:
        raise HTTPException(400, "confidence_threshold is required")
    
    return await update_camera_settings_handler(camera_id, payload.confidence_threshold, db)



@router.post("/{camera_id}/zones", response_model=ZoneResponse, status_code=201)
async def create_zone(

    camera_id: UUID,
    payload: CreateZoneRequest,
    claims: dict = Depends(get_current_user),
    db: DbSession = None

):
    
    """Adding a detection zone polygin to a camera"""

    require_role(claims, ZONE_EDITOR_ROLES)

    return await create_zone_handler(camera_id, payload.name, payload.polygon, db)




@router.delete("/{camera_id}/zones/{zone_id}", status_code=204)
async def delete_zone(

    camera_id: UUID,
    zone_id: UUID,
    claims: dict = Depends(get_current_user),
    db: DbSession = None

    
):
    
    """Removing a detection zone from a camera"""

    require_role(claims, ZONE_EDITOR_ROLES)

    return await delete_zone_handler(camera_id, zone_id, db)

