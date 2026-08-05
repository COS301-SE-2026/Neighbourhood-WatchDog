from enum import Enum

from app.core.database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Index, String, text, Enum as SAEnum, TIMESTAMP, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class CameraVisibilityEnum(str, Enum):
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    PRIVATE = "PRIVATE"


class Camera(Base):
    __tablename__ = "camera"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id"), nullable=False)
    name = Column(String, nullable=False)
    visibility = Column(SAEnum(CameraVisibilityEnum, name="camera_visibility"), nullable=False, server_default="PRIVATE")
    location = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    confidence_threshold = Column(Float, nullable=False, default=0.5, server_default="0.5")
    enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    
    alerts = relationship("Alert", back_populates="camera")
    retention_policy = relationship(
        "RetentionPolicy", 
        back_populates="camera", 
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,)
    detection_zones = relationship("CameraDetectionZone", back_populates="camera", cascade="all, delete-orphan")
    property = relationship("Property", back_populates="camera")

    __table_args__ = (
        Index("ix_camera_property_visibility", "property_id", "visibility"),
    )
