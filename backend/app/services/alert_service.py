from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.detection_event import DetectionEvent
from app.schemas.alert import AlertCreate


async def create_alert(db: Session, data: AlertCreate):
    try:
        detection_event = DetectionEvent(
            camera_id=data.camera_id,
            frame_timestamp=data.timestamp,
            detection_type=data.detection_type,
            confidence_score=data.confidence,
            thumbnail_url=data.thumbnail_url,
            processed=False,
        )
        db.add(detection_event)
        db.flush()

        alert = Alert(
            camera_id=data.camera_id,
            detection_event_id=detection_event.id,
            status="OPEN",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        return alert
    except Exception as e:
        db.rollback()
        raise e