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
    ZoneResponse,
    UpdateCameraSettingsResponse
)

from app.services.camera_settings_service import (
    create_zone_handler,
    delete_zone_handler,
    get_camera_settings_handler,
    update_camera_settings_handler
)


router = APIRouter(prefix="/cameras", tags=["camera-settings"])


Claims = Annotated[dict, Depends(get_current_user)]


@router.get(
    "/{camera_id}/settings",
    response_model=CameraSettingsResponse,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Camera not found"},
        500: {"description": "Failed to retrieve camera settings"},
    },
)
async def get_settings(camera_id: UUID, db: DbSession, claims: Annotated[dict, Depends(require_role("NEIGHBOURHOOD_ADMIN", "PROPERTY_ADMIN", "SYSTEM_ADMIN"))]):
    """Getting the confidence threshold and detection zones for a camera"""
    return await get_camera_settings_handler(camera_id, db)


@router.patch(
    "/{camera_id}/settings",
    response_model=UpdateCameraSettingsResponse,
    responses={
        400: {"description": "confidence_threshold is required"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Camera not found"},
        500: {"description": "Failed to update camera settings"},
    },
)
async def update_settings(
    camera_id: UUID,
    payload: UpdateCameraSettingsRequest,
    db: DbSession,
    claims: Annotated[dict, Depends(require_role("NEIGHBOURHOOD_ADMIN", "PROPERTY_ADMIN", "SYSTEM_ADMIN"))],
):
    """Updating the confidence threshold for a camera"""

    if payload.confidence_threshold is None:
        raise HTTPException(400, "confidence_threshold is required")
    return await update_camera_settings_handler(camera_id, payload.confidence_threshold, db, claims)


@router.post("/{camera_id}/zones", response_model=ZoneResponse, status_code=201,
    responses={
        400: {"description": "Zone polygon must contain at least 3 points"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Camera not found"},
        500: {"description": "Failed to create detection zone"},
    }
)
async def create_zone(
    camera_id: UUID,
    payload: CreateZoneRequest,
    db: DbSession,
    claims: Annotated[dict, Depends(require_role("NEIGHBOURHOOD_ADMIN", "PROPERTY_ADMIN", "SYSTEM_ADMIN"))],
):
    """Adding a detection zone polygon to a camera"""
    return await create_zone_handler(camera_id, payload.name, payload.polygon, db, claims)


@router.delete(
    "/{camera_id}/zones/{zone_id}",
    status_code=204,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Zone not found"},
        500: {"description": "Failed to delete detection zone"},
    },
)
async def delete_zone(
    camera_id: UUID,
    zone_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(require_role("NEIGHBOURHOOD_ADMIN", "PROPERTY_ADMIN", "SYSTEM_ADMIN"))],
):
    """Removing a detection zone from a camera"""
    return await delete_zone_handler(camera_id, zone_id, db, claims)