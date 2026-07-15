from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.database import DbSession
from sqlalchemy import select, func

from app.models.alert import Alert
from app.models.camera import Camera
from app.models.detection_event import DetectionEvent, DetectionType

SEVERITY_WEIGHTS = {
    DetectionType.WEAPON_DETECTED: 10,
    DetectionType.FALL_DETECTED: 8,
    DetectionType.LOITERING: 5,
    DetectionType.PERIMETER_SCAN: 4,
    DetectionType.HUMAN_PRESENCE: 2
}

def calculate_risk_score_handler(neighbourhood_id: UUID, db: DbSession):
    window_start = datetime.now(timezone.utc) - timedelta(hours=24)

    stmt = (
        select(DetectionEvent.detection_type, func.count().label("count"))
        .select_from(Alert)
        .join(Camera, Alert.camera_id == Camera.id)
        .join(DetectionEvent, Alert.detection_event_id == DetectionEvent.id)
        .where(Camera.neighbourhood_id == neighbourhood_id)
        .where(Alert.created_at >= window_start)
        .group_by(DetectionEvent.detection_type)
    )

    rows = db.execute(stmt).all()

