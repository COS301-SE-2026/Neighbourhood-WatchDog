from enum import Enum
import uuid

from app.core.database import Base
from sqlalchemy import Column, ForeignKey, String, text, Enum as SAEnum, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID


class CameraVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    PRIVATE = "PRIVATE"


class Camera(Base):
    __tablename__ = "camera"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id"), nullable=False)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id"), nullable=False)
    visibility = Column(SAEnum(CameraVisibility, name="camera_visibility"), nullable=False, server_default="PRIVATE")
    location = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
