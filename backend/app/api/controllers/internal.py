#internal endpoints for ai service communication
#no auth, just protected by network boundary
#TODO: add auth to these endpoints as it is no longer protected by network boundary

import traceback
import logging

from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.core.database import DbSession
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.alert import DetectionType


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


@router.post("/alerts", status_code=201, responses={404: {"description": "Camera not found"}})
async def create_alert(
    body: CreateAlertRequest,
    db: DbSession
) -> dict:
    """creates a detection event and alert record
        called by the ai service when the weapon is detected
        returns a new detection event id and alert id"""
    
    try:
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

        stmt = select(Camera).where(Camera.id == body.camera_id)
        result = await db.execute(stmt)
        camera: Camera | None = result.scalar_one_or_none()

        if not camera:
            logger.warning("internal create_alert: no camera found for camera_id=%s", body.camera_id)
            raise HTTPException(status_code=404,detail=f"Camera {body.camera_id} not found")

        alert = Alert(
            camera_id=UUID(body.camera_id),
            frame_timestamp=body.frame_timestamp or datetime.now(timezone.utc),
            detection_type=det_type,
            confidence_score=body.confidence_score,
            thumbnail_url=body.thumbnail_url,
            processed=True,
            status="OPEN"
        )

        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        await db.flush() #populating event id before creating the alert

        logger.info("internal create_alert: successfully created alert with alert_id=%s", str(alert.id))
        return {
            "detection_event_id": str(alert.id),
            "alert_id": str(alert.id)
        }

    except Exception:
        logger.error(f"INTERNAL ENDPOINT ERROR: {traceback.format_exc()}")
        raise



@router.patch("/alerts/{alert_id}/clip", responses={404: {"description": "Alert not found"}})
async def update_clip(alert_id: str, body: UpdateClipRequest, db: DbSession):
    """updating s3 clip key and expiry on a detection event after ai uploads the clip"""

    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        logger.warning("internal update_clip: alert with alert id=%s not found.", alert_id)
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    alert.clip_s3_key = body.clip_s3_key
    alert.clip_expires_at = datetime.fromisoformat(body.clip_expires_at)

    await db.commit()
    await db.refresh(alert)

    logger.info("internal update_clip: clip with alert_id=%s successfully updated.", alert_id)
    return{
        "alert_id": str(alert.id),
        "clip_s3_key": alert.clip_s3_key,
        "clip_expires_at": alert.clip_expires_at
    }
