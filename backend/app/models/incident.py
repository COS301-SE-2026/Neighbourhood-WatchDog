import uuid

from sqlalchemy import Column, DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incident"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))

    detection_type = Column(String(64), nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    alerts = relationship(
        "Alert",
        back_populates="incident",
        order_by="(Alert.frame_timestamp, Alert.created_at, Alert.id)",
    )

    __table_args__ = (
        Index(
            "ix_incident_detection_last_seen",
            "detection_type",
            "last_seen_at",
        ),
    )