
from fastapi import APIRouter, Depends, status

from app.schemas.camera import RegisterCameraReq, RegisterCameraRes, CamerasRes, DeregisterCameraReq, DeregisterCameraRes
from app.services.camera_service import register_camera_handler, list_cameras_handler, deregister_camera_handler
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role

router = APIRouter(prefix="/camera", tags=["cameras"])


@router.post("/register-camera")
async def register_camera(req: RegisterCameraReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Creates a new camera and links it to the property of the user."""
    
    require_role(claims = claims, allowed_roles= ['RESIDENT'])
    new_camera = await register_camera_handler(req, db, claims)

    return RegisterCameraRes(
        status=201,
        message="Camera Created Successfully",
        data=new_camera,
    )

@router.delete("deregister-camera", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_camera(req: DeregisterCameraReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Permanently remove a camera from a users property and the system."""
    require_role(claims = claims, allowed_roles= ['RESIDENT'])

    await deregister_camera_handler(req, db, claims)

    return DeregisterCameraRes(
        message="Camera Created Successfully",
        data=[],
    )

@router.get("/property/{property_id}")
async def get_property_cameras(
    property_id: str,
    db: DbSession,
    claims: dict = Depends(get_current_user),
) -> CamerasRes:
    require_role(claims, ["RESIDENT"])
    return await list_cameras_handler(property_id, db, claims)