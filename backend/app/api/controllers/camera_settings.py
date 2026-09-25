from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.core.database import DbSession
from app.schemas.camera_settings import (
    CameraSettingsResponse,
    CreateZoneRequest,
    UpdateCameraSettingsRequest,
    UpdateCameraSettingsResponse,
    ZoneResponse,
)
from app.services.camera_settings_service import (
    create_zone_handler,
    delete_zone_handler,
    get_camera_settings_handler,
    update_camera_settings_handler,
)
from app.schemas.camera_coverage import CameraCoverageInput, CameraCoverageResponse
from app.services.camera_coverage_service import (
    delete_camera_coverage_handler,
    get_camera_coverage_handler,
    upsert_camera_coverage_handler,
)
from app.auth.authorization import (
    CameraAdminClaims,
    CameraCoverageAdminClaims,
)

router = APIRouter(prefix="/cameras", tags=["camera-settings"])


# Claims = Annotated[dict, Depends(get_current_user)]


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
async def get_settings(camera_id: UUID, db: DbSession, claims: CameraAdminClaims):
    """Getting the confidence threshold and detection zones for a camera"""
    return await get_camera_settings_handler(camera_id, db, claims)


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
    claims: CameraAdminClaims,
):
    """Updating the confidence threshold for a camera"""

    if payload.confidence_threshold is None:
        raise HTTPException(400, "confidence_threshold is required")
    return await update_camera_settings_handler(camera_id, payload.confidence_threshold, db, claims)

@router.get(
    "/{camera_id}/coverage",
    response_model=CameraCoverageResponse | None,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Camera not found"},
    },
)
async def get_coverage(
    camera_id: UUID,
    db: DbSession,
    claims: CameraCoverageAdminClaims,
):
    return await get_camera_coverage_handler(camera_id, db, claims)


@router.put(
    "/{camera_id}/coverage",
    response_model=CameraCoverageResponse,
    status_code=200,
    responses={
        400: {"description": "Invalid coordinates or camera origin is too far from the property"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Camera not found"},
    },
)
async def put_coverage(
    camera_id: UUID,
    payload: CameraCoverageInput,
    db: DbSession,
    claims: CameraCoverageAdminClaims,
):
    return await upsert_camera_coverage_handler(camera_id, payload, db, claims)


@router.delete(
    "/{camera_id}/coverage",
    status_code=204,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Camera not found"},
    },
)
async def delete_coverage(
    camera_id: UUID,
    db: DbSession,
    claims: CameraCoverageAdminClaims,
):
    await delete_camera_coverage_handler(camera_id, db, claims)

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
    claims: CameraAdminClaims,
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
    claims: CameraAdminClaims,
):
    """Removing a detection zone from a camera"""
    return await delete_zone_handler(camera_id, zone_id, db, claims)