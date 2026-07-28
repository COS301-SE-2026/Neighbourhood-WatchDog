import base64
import hashlib
import hmac
import os
import re

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, Select
from pydantic import BaseModel
from typing import Annotated

from app.core.database import DbSession
from app.models.camera import Camera
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.auth.dependencies import get_authenticated_edge_agent
from app.services.rtsp_encryption import decrypt_rtsp_url


router = APIRouter(prefix="/internal", tags=["internal"])

_CAMERA_PATH_PATTERN = re.compile(r"^cameras/([0-9a-fA-F-]{36})$")


class MediaMtxAuthRequest(BaseModel):
    user: str = ""
    password: str = ""
    action: str = ""
    path: str = ""
    protocol: str = ""
    ip: str = ""
    id: str = ""
    query: str = ""



def _publish_master_key() -> bytes:
    value = os.getenv("MEDIAMTX_PUBLISH_MASTER_KEY")

    if not value:
        raise RuntimeError("MEDIAMTX_PUBLISH_MASTER_KEY is not configured.")

    return value.encode("utf-8")


def _camera_publish_credentials(camera_id: str) -> tuple[str, str]:

    username = f"camera-{camera_id}"

    digest = hmac.new(_publish_master_key(), camera_id.encode("utf-8"), hashlib.sha256).digest()


    password = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    return username, password

@router.get(
    "/cameras/enabled", 
    summary="List enabled cameras for the AI worker"
)
def list_enabled_cameras(
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
) -> dict:

    stmt = Select(Camera).where(
        Camera.property_id == credential.property_id,
        Camera.enabled.is_(True)
    ).order_by(Camera.created_at.asc())
    cameras = db.execute(stmt).scalars().all()

    data = []

    for camera in cameras:
        camera_id = str(camera.id)

        publish_username, publish_password = (_camera_publish_credentials(camera_id))

        data.append(
            {
                "id": camera.id, 
                "rtsp_url": decrypt_rtsp_url(camera.rtsp_url),
                "enabled": camera.enabled, 
                "neighbourhood_id": str(camera.neighbourhood_id) if camera.neighbourhood_id else None, 
                "confidence_threshold": camera.confidence_threshold, 
                "publish_username": publish_username, 
                "publish_password": publish_password
            }
        )

    return {"data": data}

@router.post(
    "/mediamtx/auth", 
    status_code=status.HTTP_204_NO_CONTENT, 
    summary="Authorize a MediaMTX action"

)
def authorize_mediamtx(request: MediaMtxAuthRequest, db: DbSession) -> Response:

    if request.action in {"read", "playback"}:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if request.action != "publish":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This MediaMTX action is not allowed.")


    match = _CAMERA_PATH_PATTERN.fullmatch(request.path)

    if match is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Publish path mist be cameras/<camera-uuid>.")

    try:
        camera_id = UUID(match.group(1))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Publish path contains an invalid camera ID.") from error


    camera = db.execute(
        select(Camera).where(
            Camera.id == camera_id, Camera.enabled.is_(True)
        )
    ).scalar_one_or_none()


    if camera is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Camera does not exist or is disabled.")

    expected_username, expected_password = (_camera_publish_credentials(str(camera_id)))


    credentials_are_valid = (hmac.compare_digest(request.user, expected_username) and hmac.compare_digest(request.password, expected_password))

    if not credentials_are_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid publish credential for the requested camera path.")


    return Response(status_code=status.HTTP_204_NO_CONTENT)