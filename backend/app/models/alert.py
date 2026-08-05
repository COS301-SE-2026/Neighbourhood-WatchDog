import uuid
from enum import Enum
from sqlalchemy import Boolean, Column, Index, String, ForeignKey, CheckConstraint, text, TIMESTAMP, Enum as SAEnum, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class DetectionType(str, Enum):
	HUMAN_PRESENCE = "HUMAN_PRESENCE"
	LOITERING = "LOITERING"
	PERIMETER_SCAN = "PERIMETER_SCAN"
	WEAPON_DETECTED = "WEAPON_DETECTED"
	FALL_DETECTED = "FALL_DETECTED"

class Alert(Base):
    __tablename__ = "alert"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("camera.id"), nullable=False)
    frame_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    detection_type = Column(SAEnum(DetectionType, name="detection_type"), nullable=False)
    confidence_score = Column(Float, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    processed = Column(Boolean, nullable=False, server_default="false")

    clip_s3_key = Column(String, nullable=True)
    clip_expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, server_default="OPEN")
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    camera = relationship("Camera", back_populates="alerts")

    __table_args__ = (
        CheckConstraint(
            "(status = 'RESOLVED' AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL) "
            "OR status != 'RESOLVED'",
            name="check_resolved_fields",
        ),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="ck_confidence_score_range"),
        Index("ix_detection_event_camera_timestamp", "camera_id", "frame_timestamp"),
    )