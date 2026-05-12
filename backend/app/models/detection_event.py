from enum import Enum

from app.core.database import Base
from sqlalchemy import Column, ForeignKey, String, Float, Boolean, text, Enum as SAEnum, TIMESTAMP, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID


class DetectionType(str, Enum):
    HUMAN_PRESENCE = "HUMAN_PRESENCE"
    LOITERING = "LOITERING"
    PERIMETER_SCAN = "PERIMETER_SCAN"
    WEAPON_DETECTED = "WEAPON_DETECTED"
    FALL_DETECTED = "FALL_DETECTED"

class DetectionEvent(Base):
    __tablename__ = "detection_event"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    camera_id = Column(UUID(as_uuid=True), ForeignKey("camera.id"), nullable=False)
    frame_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    detection_type = Column(SAEnum(DetectionType, name="detection_type"), nullable=False)
    confidence_score = Column(Float, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    processed = Column(Boolean, nullable=False, server_default="false")

    __table_args__ = (
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="ck_confidence_score_range"),
    )