from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.database import DbSession
from sqlalchemy import select, func

from app.models.alert import Alert
from app.models.camera import Camera
from app.models.detection_event import DetectionEvent, DetectionType
from app.models.risk_score_history import RiskLevel, RiskScoreHistory
from app.models.risk_threshold_config import RiskThresholdConfig

SEVERITY_WEIGHTS = {
    DetectionType.WEAPON_DETECTED: 10,
    DetectionType.FALL_DETECTED: 8,
    DetectionType.LOITERING: 5,
    DetectionType.PERIMETER_SCAN: 4,
    DetectionType.HUMAN_PRESENCE: 2
}

CRITICAL_DETECTION_TYPES = {
    DetectionType.WEAPON_DETECTED,
    DetectionType.FALL_DETECTED
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

    score = 0.0
    alert_count = 0
    critical_event_detected = False

    for detection_type, count in rows:
        weight = SEVERITY_WEIGHTS.get(detection_type, 0)
        score += weight * count
        alert_count += count
        if detection_type in CRITICAL_DETECTION_TYPES and count > 0:
            critical_event_detected = True

    threshold_stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id == neighbourhood_id)
    threshold = db.execute(threshold_stmt).scalar_one_or_none()

    if not threshold:
        default_stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id.is_(None))
        threshold = db.execute(default_stmt).scalar_one()

    if score <= threshold.low_max:
        classification = RiskLevel.LOW
    elif score <= threshold.medium_max:
        classification = RiskLevel.MEDIUM
    else:
        classification = RiskLevel.HIGH

    #override
    if critical_event_detected:
        classification = RiskLevel.HIGH

    new_score = RiskScoreHistory(
        neighbourhood_id=neighbourhood_id,
        score=score,
        classification=classification,
        alert_count=alert_count
    )

    db.add(new_score)
    db.commit()
    db.refresh(new_score)

    return new_score
