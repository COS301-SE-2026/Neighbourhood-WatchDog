from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.camera import RegisterCameraReq, RegisterCameraRes, CamerasRes, CameraEditReq, EditCameraRes
from app.services.camera_service import register_camera_handler, list_cameras_handler, deregister_camera_handler, edit_camera_handler
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.dependencies import require_role
from app.auth.authorization import Claims, CameraAdminClaims, PropertyMemberClaims, is_property_admin

router = APIRouter(prefix="/camera", tags=["cameras"])


@router.post(
    "/register-camera",
    response_model=RegisterCameraRes,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Property not found"},
        500: {"description": "Could not register camera"},
    },
)
async def register_camera(
    req: RegisterCameraReq,
    db: DbSession,
    claims: Claims,
) -> RegisterCameraRes:
    """Creates a new camera and links it to the property of the user."""
    allowed =await is_property_admin(req.property_id, claims, db)
    if not allowed:
        raise HTTPException(status_code=403, detail="You do not have permission to add a camera to this property")
    
    new_camera = await register_camera_handler(req, db, claims)

    return RegisterCameraRes(
        status=201,
        message="Camera Created Successfully",
        data=new_camera,
    )

@router.delete(
    "/{camera_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Forbidden"},
        404: {"description": "Camera not found"},
        500: {"description": "Could not deregister camera"},
    },
)
async def deregister_camera(camera_id: UUID,
    db: DbSession,
    claims: CameraAdminClaims,
):
    """Permanently remove a camera from a users property and the system."""
    
    
    await deregister_camera_handler(camera_id, db, claims)

@router.get(
    "/property/{property_id}",
    response_model=CamerasRes,
    responses={
        400: {"description": "Invalid property ID"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Property does not exist or user does not have access"},
        500: {"description": "No database session"},
    },
)
async def get_property_cameras(
    property_id: str,
    db: DbSession,
    claims: PropertyMemberClaims,
) -> CamerasRes:
    
    return await list_cameras_handler(property_id, db, claims)

@router.patch(
    "/{camera_id}",
    response_model=EditCameraRes,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "No fields provided to update"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Forbidden"},
        404: {"description": "Camera not found"},
        500: {"description": "Failed to update camera"},
    },
)
async def edit_camera(
    camera_id: UUID, 
    req: CameraEditReq,
    db: DbSession, 
    claims: CameraAdminClaims
) -> EditCameraRes:
    """Edit a camera"""

    updated = await edit_camera_handler(camera_id, req, db, claims)

    return await EditCameraRes(
        status=200,
        message="Camera updated successfully",
        data=updated
    )

