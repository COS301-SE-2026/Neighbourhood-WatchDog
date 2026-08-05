#internal endpoints for ai service communication
#no auth, just protected by network boundary

import traceback

from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.database import DbSession
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.alert import DetectionType


router = APIRouter(prefix="/internal", tags=["internal"])


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

#creates a detection event and alert record
#called by the ai service when the weapon is detected
#returns a new detection event id and alert id
def create_alert(body: CreateAlertRequest, db: DbSession):

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


        camera: Camera | None = db.query(Camera).filter_by(
            id=body.camera_id
        ).first()



        if not camera:
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
        db.commit()
        db.refresh(alert)
        db.flush() #populating event id before creating the alert



        return {
            "detection_event_id": str(alert.id),
            "alert_id": str(alert.id)

        }

    except Exception:
        print(f"INTERNAL EDNPOINT ERROR: {traceback.format_exc()}", flush=True)
        raise



@router.patch("/alerts/{alert_id}/clip", responses={404: {"description": "Alert not found"}})

#updating s3 clip key and expiry on a detection event after ai uploads the clip
def update_clip(alert_id: str, body: UpdateClipRequest, db: DbSession):

    alert = db.query(Alert).filter_by(id=alert.id).one_or_none()


    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"

        )

    alert.clip_s3_key = body.clip_s3_key
    alert.clip_expires_at = datetime.fromisoformat(body.clip_expires_at)

    db.commit()
    db.refresh(alert)


    return{
        "alert_id": str(alert.id),
        "clip_s3_key": alert.clip_s3_key,
        "clip_expires_at": alert.clip_expires_at
    }
