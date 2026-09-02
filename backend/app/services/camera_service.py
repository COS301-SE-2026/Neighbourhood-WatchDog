from app.schemas.camera import CameraRes, CameraListItemRes, CamerasRes, CameraEditReq
from app.models.camera import Camera
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import User
from app.services.rtsp_encryption import encrypt_rtsp_url, decrypt_rtsp_url
from app.models.edge_agent_credentials import EdgeAgentCredential
from datetime import datetime, timezone
from app.services.audit_service import create_audit_log_item

from fastapi import Response, status
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from app.models.audit_log import AuditAction, TargetEntity
from app.schemas.camera import (
    EnabledCamerasRes,
    ListEnabledCameras,
    MediaMtxAuthRequest,
)
import base64
import hashlib
import hmac
import os
import logging
import re

logger = logging.getLogger(__name__)

NO_DB_SESSION = "No database session"
NOT_AUTHENTICATED = "Not authenticated"
EDGE_AGENT_TIMEOUT_SECONDS = float(os.getenv("FAILOVER_AGENT_TIMEOUT_SECONDS", "30"))


def _edge_agent_is_available(last_seen_at: datetime | None) -> bool | None:
    if last_seen_at is None:
        return None

    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)

        age_seconds = (datetime.now(timezone.utc) - last_seen_at).total_seconds()


    return age_seconds <= EDGE_AGENT_TIMEOUT_SECONDS


_CAMERA_PATH_PATTERN = re.compile(r"^cameras/([0-9a-fA-F-]{36})$")


def _publish_master_key() -> bytes:
    value = os.getenv("MEDIAMTX_PUBLISH_MASTER_KEY")

    if not value:
        raise RuntimeError("MEDIAMTX_PUBLISH_MASTER_KEY is not configured.")

    return value.encode("utf-8")


def _camera_publish_credentials(camera_id: str) -> tuple[str, str]:
    """Helper function which recevies a camera_id creates a username and password for the camera and returns them as a tuple"""
    username = f"camera-{camera_id}"
    digest = hmac.new(_publish_master_key(), camera_id.encode("utf-8"), hashlib.sha256).digest()
    password = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    return username, password

async def register_camera_handler(req, db, claims):
    """Register a camera for an authorised property user and audit the creation."""
    if not db:
        raise HTTPException(500, NO_DB_SESSION)
    if not claims:
        raise HTTPException(401, NOT_AUTHENTICATED)

    try:
        result = await db.execute(select(Property).where(Property.id == req.property_id))
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(404, "Property not found")

        # encrypting the rtsp url
        plaintext_rtsp_url = req.rtsp_url
        ciphertext_rtsp_url = encrypt_rtsp_url(plaintext_rtsp_url)

        new_camera = Camera(
            property_id=req.property_id,
            name=req.name,
            rtsp_url=ciphertext_rtsp_url,
            visibility=req.visibility,
            location=req.location,
        )
        db.add(new_camera)

        logger.info(
            "Camera registered: camera_id=%s, property_id=%s",
            new_camera.id,
            new_camera.property_id,
        )

        # Get ID before commit
        await db.flush()

        await create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.CREATE,
            target_entity_type=TargetEntity.CAMERA,
            target_entity_id=new_camera.id,
            new_values={
                "property_id": str(new_camera.property_id),
                "name": new_camera.name,
                "visibility": new_camera.visibility,
                "location": new_camera.location,
            },
        )

        await db.commit()
        await db.refresh(new_camera)

        return CameraRes(
            id=new_camera.id,
            name=new_camera.name,
            property_id=new_camera.property_id,
            neighbourhood_id=property_obj.neighbourhood_id,
            rtsp_url=new_camera.rtsp_url,
            visibility=new_camera.visibility,
            location=new_camera.location,
            enabled=new_camera.enabled,
            created_at=new_camera.created_at,
        )

    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Could not register camera")
    except HTTPException as he:
        await db.rollback()
        raise he

async def deregister_camera_handler(camera_id, db, claims):
    """Remove an authorised user's camera and audit the deletion."""
    if not db:
        raise HTTPException(status_code=500, detail=NO_DB_SESSION)
    if not claims:
        raise HTTPException(status_code=500, detail=NOT_AUTHENTICATED)
    
    try:
        result = await db.execute(select(Camera).where(Camera.id == camera_id))
        camera_obj = result.scalar_one_or_none()

        if not camera_obj:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        prop_user_result = await db.execute(
            select(PropertyUser)
            .options(joinedload(PropertyUser.user))
            .join(PropertyUser.user)
            .where(PropertyUser.property_id == camera_obj.property_id, User.cognito_sub == claims.get("sub"))
        )
        prop_user = prop_user_result.scalar_one_or_none()

        if prop_user is None or getattr(getattr(prop_user, "user", None), "cognito_sub", None) != claims.get("sub"):
            raise HTTPException(status_code=403, detail="Forbidden")

        
        old_values = {
            "property_id": str(camera_obj.property_id),
            "name": camera_obj.name,
            "visibility": camera_obj.visibility,
            "location": camera_obj.location,
        }

        await db.delete(camera_obj)

        await create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.DELETE,
            target_entity_type=TargetEntity.CAMERA,
            target_entity_id=camera_obj.id,
            old_values=old_values,
        )

        await db.commit()
        
    except HTTPException as he:
        await db.rollback()
        raise he
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Could not deregister camera")
    except Exception:
        await db.rollback()
        raise HTTPException(500, "Failed to delete camera")
    
async def edit_camera_handler(
    camera_id: UUID, 
    req: CameraEditReq,
    db: AsyncSession, 
    claims: dict
    ) -> CameraRes:
    """Update an authorised user's camera details and audit the changes."""

    
    try:

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided to update")
    
        result = await db.execute(select(Camera).where(Camera.id == camera_id))
        camera_obj = result.scalar_one_or_none()

        if not camera_obj:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        prop_user_result = await db.execute(
            select(PropertyUser)
            .join(PropertyUser.user)
            .where(
                PropertyUser.property_id == camera_obj.property_id,
                User.cognito_sub == claims.get("sub")
                
                )
            )
        prop_user = prop_user_result.scalar_one_or_none()
        
        if not prop_user:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        old_values = {
            field: getattr(camera_obj, field)
            for field in update_data.keys()
        }


        for field, value in update_data.items():
            setattr(camera_obj, field, value)


        new_values = {
            field: getattr(camera_obj, field)
            for field in update_data.keys()
        }


        await create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.UPDATE,
            target_entity_type=TargetEntity.CAMERA,
            target_entity_id=camera_obj.id,
            old_values=old_values,
            new_values=new_values,
        )


        await db.commit()
        await db.refresh(camera_obj)

        return CameraRes(
            id=camera_obj.id,
            name=camera_obj.name,
            property_id=camera_obj.property_id,
            neighbourhood_id=camera_obj.neighbourhood_id,
            rtsp_url=camera_obj.rtsp_url,
            visibility=camera_obj.visibility,
            location=camera_obj.location,
            enabled=camera_obj.enabled,
            created_at=camera_obj.created_at,
        )
    
    except HTTPException as he:
        await db.rollback()
        raise he
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update camera")



async def list_cameras_handler(property_id, db, claims):
    """Return cameras belonging to a property accessible to the requesting user."""
    if not db:
        raise HTTPException(500, NO_DB_SESSION)

    if not claims:
        raise HTTPException(401, NOT_AUTHENTICATED)

    try:
        prop_uuid = UUID(property_id)
    except ValueError:
        raise HTTPException(400, "Invalid property ID")

    stmt = select(Property).where(Property.id == prop_uuid)
    result = await db.execute(stmt)
    property_obj = result.scalar_one_or_none()

    if not property_obj:
        raise HTTPException(403, "Property does not exist")

    prop_user_result = await db.execute(
        select(PropertyUser)
        .options(joinedload(PropertyUser.user))
        .where(PropertyUser.property_id == prop_uuid)
    )
    prop_user = prop_user_result.scalar_one_or_none()

    if not prop_user or prop_user.user.cognito_sub != claims.get("sub"):
        raise HTTPException(
            status_code=403,
            detail="This user does not have access to this property",
        )

    stmt = select(Camera).where(Camera.property_id == prop_uuid).order_by(Camera.created_at.desc())
    result = await db.execute(stmt)
    cameras = result.scalars().all()

    heartbeat_result = await db.execute(
        select(
            EdgeAgentCredential.property_id, func.max(EdgeAgentCredential.last_seen_at).label("last_seen_at")
        )
        .where(
            EdgeAgentCredential.property_id == prop_uuid, EdgeAgentCredential.revoked_at.is_(None)
        )
        .group_by(EdgeAgentCredential.property_id)
    )

    last_seen_by_property = {
        property_id: last_seen_at
        for property_id, last_seen_at in heartbeat_result.all()
    }

    return CamerasRes(
        status=200,
        message="Cameras fetched successfully",
        data=[
            CameraListItemRes(
                id=c.id,
                name=c.name,
                property_id=c.property_id,
                neighbourhood_id=property_obj.neighbourhood_id,
                rtsp_url=decrypt_rtsp_url(c.rtsp_url),
                visibility=c.visibility,
                location=c.location,
                enabled=c.enabled,
                created_at=c.created_at,
                edge_agent_available=_edge_agent_is_available(last_seen_by_property.get(c.property_id))
            )
            for c in cameras
        ],
    )

async def list_enabled_cameras_for_agent_handler(property_id: UUID, db:AsyncSession) -> ListEnabledCameras:
    """Returns enabled cameras available to an authenticated AI worker."""

    stmt = (
    select(Camera)
        .options(joinedload(Camera.property), selectinload(Camera.detection_zones))
        .where(
            Camera.property_id == property_id,
            Camera.enabled.is_(True)
        )
        .order_by(Camera.created_at.asc())
    )
    result = await db.execute(stmt)
    cameras = result.scalars().all()

    data: list[EnabledCamerasRes] = []

    for camera in cameras:
        camera_id = str(camera.id)

        publish_username, publish_password = (_camera_publish_credentials(camera_id))
        

        data.append(
            EnabledCamerasRes(
                id=camera.id,
                rtsp_url=decrypt_rtsp_url(camera.rtsp_url),
                enabled=camera.enabled,
                neighbourhood_id=camera.property.neighbourhood_id,
                confidence_threshold=camera.confidence_threshold,
                zones=[zone.polygon for zone in camera.detection_zones],
                publish_username=publish_username,
                publish_password=publish_password,
            )
        )
        
    return ListEnabledCameras(data=data)


async def authorize_mediamtx_for_agent_handler(request: MediaMtxAuthRequest, db:AsyncSession) -> Response:
    """Authorise a MediaMTX playback or camera publishing action."""

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


    result = await db.execute(
        select(Camera).where(
            Camera.id == camera_id, Camera.enabled.is_(True)
        )
    )

    camera = result.scalar_one_or_none()


    if camera is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Camera does not exist or is disabled.")

    expected_username, expected_password = (_camera_publish_credentials(str(camera_id)))


    credentials_are_valid = (hmac.compare_digest(request.user, expected_username) and hmac.compare_digest(request.password, expected_password))

    if not credentials_are_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid publish credential for the requested camera path.")


    return Response(status_code=status.HTTP_204_NO_CONTENT)