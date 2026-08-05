#internal endpoints for ai service communication
#uses API for auth

import traceback
import logging

from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from typing import Annotated

from app.core.database import DbSession
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.alert import DetectionType
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.auth.dependencies import get_authenticated_edge_agent

router = APIRouter(prefix="/internal", tags=["internal"])
logger = logging.getLogger(__name__)

class CreateAlertRequest(BaseModel):
    camera_id: str
    detection_type: str
    confidence_score: float
    thumbnail_url: str | None = None
    frame_timestamp: str | None = None


class UpdateClipRequest(BaseModel):
    clip_s3_key: str
    clip_expires_at: str ##the iso datetime


@router.post("/alerts",
    status_code=201,
    responses={
        404: {"description": "Camera not found"}, 
        400: {"description": "camera_id is not a valid UUID, or frame_timestamp is not a valid IOS datetime"},
        401: {"description": "Invalid or revoked edge agent credential"},
    },
)
async def create_alert(
    body: CreateAlertRequest,
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
      # this line ^ is in charge of checking whether there is a valid api key associated with this or not
) -> dict:
    """creates a detection event and alert record
        called by the ai service (on the edge agent) when the weapon is detected
        returns a new detection event id and alert id"""
    
    label_map = {
        "gun": DetectionType.WEAPON_DETECTED,
        "knife": DetectionType.WEAPON_DETECTED,
        "grenade": DetectionType.WEAPON_DETECTED,
        "explosion": DetectionType.WEAPON_DETECTED
    }

    try:
        det_type = DetectionType(body.detection_type.upper())
    except ValueError:
        det_type = label_map.get(body.detection_type.lower(), DetectionType.WEAPON_DETECTED)

    try:
        camera_id = UUID(body.camera_id)
    except ValueError:
        logger.warning("internal create_alert: malformed camera_id=%s", body.camera_id)
        raise HTTPException(status_code=400, detail="camera_id is not a valid UUID")

    if body.frame_timestamp:
        try:
            frame_timestamp = datetime.fromisoformat(body.frame_timestamp)
        except ValueError:
            logger.warning("internal create_alert: malformed frame_timestamp=%s", body.frame_timestamp)
            raise HTTPException(status_code=400, detail="frame_timestamp is not a valid ISO datetime")
    else:
        frame_timestamp = datetime.now(timezone.utc)

    try:

        stmt = select(Camera).where(Camera.id == body.camera_id)
        result = await db.execute(stmt)
        camera: Camera | None = result.scalar_one_or_none()

        if not camera:
            logger.warning("internal create_alert: no camera found for camera_id=%s", body.camera_id)
            raise HTTPException(status_code=404,detail=f"Camera {body.camera_id} not found")

        
        alert = Alert(
            camera_id=camera_id,
            frame_timestamp= frame_timestamp,
            detection_type=det_type,
            confidence_score=body.confidence_score,
            thumbnail_url=body.thumbnail_url,
            processed=True,
            status="OPEN"
        )

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        logger.info("internal create_alert: successfully created alert with alert_id=%s", str(alert.id))
        return {
            "detection_event_id": str(alert.id),
            "alert_id": str(alert.id)
        }
        #TODO: Turn this dict into an actual pydantic response class object
    
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"INTERNAL ENDPOINT ERROR: {traceback.format_exc()}")
        raise



@router.patch("/alerts/{alert_id}/clip", 
    responses={
        404: {"description": "Alert not found"}, 
        400: {"description": "alert_id is not a valid UUID, or clip_expires_at is not a valid IOS datetime"},
        401: {"description": "Invalid or revoked edge agent credential"},
    }
)
async def update_clip(
    alert_id: str, 
    body: UpdateClipRequest, 
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
) -> dict:
    """updating s3 clip key and expiry on a detection event after ai uploads the clip"""

    try:
        alert_uuid = UUID(alert_id)
    except ValueError:
        logger.warning("internal update_clip: malformed alert_id=%s", alert_id)
        raise HTTPException(status_code=400, detail="alert_id is not a valid UUID")

    try:
        clip_expires_at = datetime.fromisoformat(body.clip_expires_at)
    except ValueError:
        logger.warning("internal update_clip: malformed clip_expires_at=%s", body.clip_expires_at)
        raise HTTPException(status_code=400, detail="clip_expires_at is not a valid ISO datetime")

    try:
        stmt = select(Alert).where(Alert.id == alert_uuid)
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()

        if not alert:
            logger.warning("internal update_clip: alert with alert id=%s not found.", alert_id)
            raise HTTPException(
                status_code=404,
                detail="Alert not found"
            )

        alert.clip_s3_key = body.clip_s3_key
        alert.clip_expires_at = clip_expires_at

        await db.commit()
        await db.refresh(alert)

        logger.info("internal update_clip: clip with alert_id=%s successfully updated.", alert_id)
        return{
            "alert_id": str(alert.id),
            "clip_s3_key": alert.clip_s3_key,
            "clip_expires_at": alert.clip_expires_at
        }
        #TODO: Turn this dict into an actual pydantic response class object

    except HTTPException:
        raise
    except Exception:
        logger.exception("internal update_clip: unexpected error updating clip for alert_id=%s", alert_id)
        raise