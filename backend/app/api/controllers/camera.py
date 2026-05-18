from fastapi import APIRouter, Depends, HTTPException
from app.schemas.camera import RegisterCameraReq, RegisterCameraRes
from app.services.property_service import register_camera_handler
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role

router = APIRouter(prefix="/camera", tags=["cameras"])

@router.post("/register-camera")
async def register_camera(req: RegisterCameraReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Creates a new camera and links it to the property of the user."""
    
    require_role(['Resident'])
    new_camera = await register_camera_handler(req, db, claims)

    return RegisterCameraRes(
        201,
        "Property Created Successful",
        new_camera
    )