from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.database import DbSession
from sqlalchemy import select, func

from app.models.alert import Alert, DetectionType
from app.models.camera import Camera
from app.models.risk_score_history import RiskLevel, RiskScoreHistory
from app.models.risk_threshold_config import RiskThresholdConfig
from app.models.property import Property
import logging

logger = logging.getLogger(__name__)

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

async def calculate_risk_score_handler(neighbourhood_id: UUID, db: DbSession):
    """Calculates neighbourhood risk score from alerts in the last 24hrs, classifies it against thresholds and stores the result"""
    
    window_start = datetime.now(timezone.utc) - timedelta(hours=24)
    logger.info("calculate_risk_score: starting calculation for neighbourhood_id=%s window_start=%s", neighbourhood_id, window_start)
    stmt = (
        select(Alert.detection_type, func.count().label("count"))
        .join(Camera, Alert.camera_id == Camera.id)
        .join(Property, Camera.property_id == Property.id)
        .where(Property.neighbourhood_id == neighbourhood_id)
        .where(Alert.created_at >= window_start)
        .group_by(Alert.detection_type)
    )

    result = await db.execute(stmt)
    rows = result.all()

    score = 0.0
    alert_count = 0
    critical_event_detected = False

    for detection_type, count in rows:
        weight = SEVERITY_WEIGHTS.get(detection_type, 0)
        score += weight * count
        alert_count += count
        if detection_type in CRITICAL_DETECTION_TYPES and count > 0:
            critical_event_detected = True
            logger.warning("calculate_risk_score: critical detection_type=%s count=%d observed for neighbour_id=%s", detection_type, count, neighbourhood_id)

    threshold_stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id == neighbourhood_id)
    threshold_result = await db.execute(threshold_stmt)
    threshold = threshold_result.scalar_one_or_none()

    if not threshold:
        logger.info("calculate_risk_score: no threshold config for neighbourhood_id=%s falling back to default", neighbourhood_id)
        default_stmt = select(RiskThresholdConfig).where(RiskThresholdConfig.neighbourhood_id.is_(None))
        default_result = await db.execute(default_stmt)
        threshold = default_result.scalar_one()

    if score <= threshold.low_max:
        classification = RiskLevel.LOW
    elif score <= threshold.medium_max:
        classification = RiskLevel.MEDIUM
    else:
        classification = RiskLevel.HIGH

    #override
    if critical_event_detected:
        if classification != RiskLevel.HIGH:
            logger.warning("calculate_risk_score: overriding classification=%s to HIGH for neighbourhood_id=%s due to critical event", classification, neighbourhood_id)
        classification = RiskLevel.HIGH

    new_score = RiskScoreHistory(
        neighbourhood_id=neighbourhood_id,
        score=score,
        classification=classification,
        alert_count=alert_count
    )

    db.add(new_score)
    await db.commit()
    await db.refresh(new_score)
    logger.info("calculate_risk_score: completed for neigbbourhood_id=%s score=%s classification=%s alert_count=%d", neighbourhood_id, score, classification, alert_count)
    return new_score
