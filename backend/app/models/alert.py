import uuid
from sqlalchemy import Column, String, ForeignKey, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
from sqlalchemy.orm import relationship
from app.core.database import Base

class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class Alert(Base):
    __tablename__ = "alert"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id          = Column(UUID(as_uuid=True), ForeignKey("camera.id"), nullable=False)
    detection_event_id = Column(UUID(as_uuid=True), ForeignKey("detection_event.id"), nullable=False)
    status             = Column(String, nullable=False, server_default="OPEN")
    resolved_by        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at        = Column(TIMESTAMPTZ, nullable=True)
    created_at         = Column(TIMESTAMPTZ, nullable=False, server_default=text("now()"))

    camera           = relationship("Camera", back_populates="alerts")
    detection_event  = relationship("DetectionEvent", back_populates="alerts")
    resolver         = relationship("User", back_populates="resolved_alerts")

    __table_args__ = (
        CheckConstraint(
            "(status = 'RESOLVED' AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL) "
            "OR status != 'RESOLVED'",
            name="check_resolved_fields"
        ),
    )