from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.controllers.detection import verify_internal_token
from app.core.database import DbSession
from app.models.camera import Camera


router = APIRouter(prefix="/internal", tags=["internal"])


@router.get(
    "/cameras/enabled", 
    dependencies=[Depends(verify_internal_token)], 
    summary="List enabled cameras for the AI worker"
)
def list_enabled_cameras(db: DbSession) -> dict:

    cameras = db.execute(
        select(Camera)
        .where(Camera.enabled.is_(True))
        .order_by(Camera.created_at.asc())
    ).scalars().all()


    return {
        "data": [
            {
                "id": str(camera.id), 
                "rtsp_url": camera.rtsp_url, 
                "enabled": camera.enabled, 
                "neighbourhood_id": str(camera.neighbourhood_id), 
                "confidence_threshold": camera.confidence_threshold
            }
            for camera in cameras
        ]
    }