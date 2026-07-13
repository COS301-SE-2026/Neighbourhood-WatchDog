#internal endpoints for ai service communication
#no auth, just protected by network boundary

import traceback

from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.database import DbSession
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.detection_event import DetectionEvent, DetectionType


router = APIRouter(prefix="/internal", tags=["internal"])


class CreateDetectionEventRequest(BaseModel):
    camera_id: str
    detection_type: str
    confidence_score: float
    thumbnail_url: str | None = None
    frame_timestamp: str | None = None


class UpdateClipRequest(BaseModel):
    clip_s3_key: str
    clip_expires_at: str ##the iso datetime


@router.post("/detection-events", status_code=201)

#creates a detection event and alert record
#called by the ai service when the weapon is detected
#returns a new detection event id and alert id
def create_detection_event(body: CreateDetectionEventRequest, db: DbSession):

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
            raise HTTPException(
                status_code=404,
                detail=f"Camera {body.camera_id} not found"
            )
        
        ts = (
            datetime.fromisoformat(body.frame_timestamp)

            if body.frame_timestamp
            else datetime.now(timezone.utc)
        )
            


        event = DetectionEvent(
            
            camera_id=UUID(body.camera_id),
            frame_timestamp=ts,
            detection_type=det_type,
            confidence_score=body.confidence_score,
            thumbnail_url=body.thumbnail_url

        )

        db.add(event)
        db.flush() #populating event id before creating the alert


        alert = Alert(
            camera_id=UUID(body.camera_id),
            detection_event_id=event.id,
            status="OPEN"

        )
        db.add(alert)
        db.commit()
        db.refresh(event)
        db.refresh(alert)


        return {
            "detection_event_id": str(event.id),
            "alert_id": str(alert.id)
                            
        }

    except Exception as e:
        print(f"INTERNAL EDNPOINT ERROR: {traceback.format_exc()}", flush=True)
        raise



@router.patch("/detection-events/{event_id}/clip")

#updating s3 clip key and expiry on a detection event after ai uploads the clip
def update_clip(event_id: str, body: UpdateClipRequest, db: DbSession):

    event: DetectionEvent | None = db.query(DetectionEvent).filter_by(
        id=event_id
    ).first()


    if not event: 
        raise HTTPException(
            status_code=404,
            detail="Detection event not found"

        )

    event.clip_s3_key = body.clip_s3_key
    event.clip_expires_at = datetime.fromisoformat(body.clip_expires_at)

    db.commit()



    return{
        "ok": True
    }
