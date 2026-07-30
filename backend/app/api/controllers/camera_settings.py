from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.auth.dependencies import require_role
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

ZONE_EDITOR_ROLES = ["NEIGHBOURHOOD_ADMIN", "PROPERTY_ADMIN", "SYSTEM_ADMIN"]

Claims = Annotated[dict, Depends(get_current_user)]


@router.get("/{camera_id}/settings", response_model=CameraSettingsResponse)
async def get_settings(camera_id: UUID, db: DbSession, claims: Claims):
    """Getting the confidence threshold and detection zones for a camera"""
    require_role(claims, ZONE_EDITOR_ROLES)
    return get_camera_settings_handler(camera_id, db)


@router.patch("/{camera_id}/settings",responses={400: {"description": "confidence_threshold is required"}})
async def update_settings(
    camera_id: UUID,
    payload: UpdateCameraSettingsRequest,
    db: DbSession,
    claims: Claims,
):
    """Updating the confidence threshold for a camera"""
    # require_role(claims, ZONE_EDITOR_ROLES)
    if payload.confidence_threshold is None:
        raise HTTPException(400, "confidence_threshold is required")
    return update_camera_settings_handler(camera_id, payload.confidence_threshold, db, claims)


@router.post("/{camera_id}/zones", response_model=ZoneResponse, status_code=201)
async def create_zone(
    camera_id: UUID,
    payload: CreateZoneRequest,
    db: DbSession,
    claims: Claims,
):
    """Adding a detection zone polygon to a camera"""
    require_role(claims, ZONE_EDITOR_ROLES)
    return create_zone_handler(camera_id, payload.name, payload.polygon, db, claims)


@router.delete("/{camera_id}/zones/{zone_id}", status_code=204)
async def delete_zone(
    camera_id: UUID,
    zone_id: UUID,
    db: DbSession,
    claims: Claims,
):
    """Removing a detection zone from a camera"""
    require_role("RESIDENT", "NEIGHBOURHOOD_ADMIN")
    return delete_zone_handler(camera_id, zone_id, db, claims)