from enum import Enum

from sqlalchemy import Boolean, CheckConstraint, Column, Enum as SAEnum, Float, ForeignKey, String, text, TIMESTAMP, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class DetectionType(str, Enum):
	HUMAN_PRESENCE = "HUMAN_PRESENCE"
	LOITERING = "LOITERING"
	PERIMETER_SCAN = "PERIMETER_SCAN"
	WEAPON_DETECTED = "WEAPON_DETECTED"
	FALL_DETECTED = "FALL_DETECTED"


class DetectionEvent(Base):
	__tablename__ = "detection_event"

	id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
	camera_id = Column(UUID(as_uuid=True), ForeignKey("camera.id", ondelete="CASCADE"), nullable=False)
	frame_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
	detection_type = Column(SAEnum(DetectionType, name="detection_type"), nullable=False)
	confidence_score = Column(Float, nullable=False)
	thumbnail_url = Column(String, nullable=True)
	processed = Column(Boolean, nullable=False, server_default="false")

	clip_s3_key = Column(String, nullable=True)
	clip_expires_at = Column(DateTime(timezone=True), nullable=True)
	

	camera = relationship("Camera", back_populates="detection_events")
	alerts = relationship("Alert", back_populates="detection_event", passive_deletes=True)

	__table_args__ = (
		CheckConstraint("confidence_score BETWEEN 0 AND 1", name="ck_confidence_score_range"),
		Index("ix_detection_event_camera_timestamp", "camera_id", "frame_timestamp"),
	)


__all__ = ["DetectionEvent", "DetectionType"]
