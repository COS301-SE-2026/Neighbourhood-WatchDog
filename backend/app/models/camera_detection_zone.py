"""
CameraDetectionZone - image-space polygon zones drawn on a camera view.

Each point in `polygon` is stored as normalized coordinates [x, y] in the
range [0.0, 1.0] relative to the camera frame dimensions. This makes the
zone resolution-independent.

Example polygon (top-left quadrant):
  [[0.0, 0.0], [0.5, 0.0], [0.5, 0.5], [0.0, 0.5]]
"""
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class CameraDetectionZone(Base):
    __tablename__ = "camera_detection_zone"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("camera.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, default="Zone")

    
    # List of [x, y] pairs, each in range [0.0, 1.0]
    polygon = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    camera = relationship("Camera", back_populates="detection_zones")
