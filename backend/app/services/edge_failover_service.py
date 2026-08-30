from __future__ import annotations

import base64
import hashlib
import hmac
import os

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.camera import Camera
from app.schemas.edge_failover import FailoverCameraRes, FailoverCamerasRes
from app.services.rtsp_encryption import decrypt_rtsp_url



FAILOVER_CONTROLLER_TOKEN = os.getenv("FAILOVER_CONTROLLER_TOKEN", "")

def _publish_master_key() -> bytes:
    value = os.getenv("MEDIAMTX_PUBLISH_MASTER_KEY")


    if not value:
        raise RuntimeError("MEDIAMTX_PUBLISH_MASTER_KEY is not configured")
    return value.encode("utf-8")


def camera_publish_credentials(camera_id: UUID | str) -> tuple[str, str]:
    """ creates the same media mtx credentials used by the edge agent"""

    camera_id_text = str(camera_id)
    username = f"camera-{camera_id_text}"
    digest = hmac.new(_publish_master_key(), camera_id_text.encode("utf-8"), hashlib.sha256).digest()
    password = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


    return username, password


def require_failover_controller_token(provided_token: str | None) -> None:

    if not FAILOVER_CONTROLLER_TOKEN:
        raise RuntimeError("FAILOVER_CONTROLLER_TOKEN is not configured")

    if not provided_token or not hmac.compare_digest(provided_token, FAILOVER_CONTROLLER_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid failover controller token")


async def list_failover_cameras(db: AsyncSession) -> FailoverCamerasRes:
    """returns enabled camera and the private connection info required by the ec2 failover controller"""

    statement = (select(Camera)
                 .where(Camera.enabled.is_(True))
                 .order_by(Camera.created_at.asc())
                )

    result = await db.execute(statement)
    cameras = result.scalars().all()

    data: list[FailoverCameraRes] = []


    for camera in cameras:
        username, password = camera_publish_credentials(camera.id)

        data.append(
            FailoverCameraRes(
                id=camera.id, 
                property_id=camera.property_id, 
                enabled=camera.enabled,
                rtsp_url=decrypt_rtsp_url(camera.rtsp_url),
                publish_username=username,
                publish_password=password
            )
        )


    return FailoverCamerasRes(data=data)


