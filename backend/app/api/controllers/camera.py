from uuid import UUID

from fastapi import APIRouter, Depends

from app.schemas.camera import RegisterCameraReq, RegisterCameraRes, CamerasRes
from app.services.camera_service import register_camera_handler, list_cameras_handler
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role

router = APIRouter(prefix="/camera", tags=["cameras"])


@router.post("/register-camera")
async def register_camera(
    req: RegisterCameraReq,
    db: DbSession,
    claims: dict = Depends(get_current_user),
) -> RegisterCameraRes:
    require_role(["Resident"])
    new_camera = await register_camera_handler(req, db, claims)

    return RegisterCameraRes(
        status=201,
        message="Camera Created Successfully",
        data=new_camera,
    )


@router.get("/property/{property_id}")
async def get_property_cameras(
    property_id: UUID,
    db: DbSession,
    claims: dict = Depends(get_current_user),
) -> CamerasRes:
    require_role(["Resident"])
    return await list_cameras_handler(property_id, db, claims)