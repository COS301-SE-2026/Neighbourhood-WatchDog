import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incident"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))

    detection_type = Column(String(64), nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)

    ended_at = Column(DateTime(timezone=True), nullable=True)

    tracking_subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracking_subject.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    alerts = relationship(
        "Alert",
        back_populates="incident",
        order_by="(Alert.frame_timestamp, Alert.created_at, Alert.id)",
    )

    tracking_subject = relationship("TrackingSubject")

    __table_args__ = (
        Index(
            "ix_incident_detection_last_seen",
            "detection_type",
            "last_seen_at",
        ),
        Index(
            "ix_incident_tracking_subject_id",
            "tracking_subject_id",
        ),
        Index(
            "ix_incident_active",
            "ended_at",
        ),
    )