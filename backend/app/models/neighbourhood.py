import uuid

from sqlalchemy import Column, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from app.core.database import Base

class Neighbourhood(Base):
    __tablename__ = "neighbourhood"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    location = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    cameras = relationship("Camera", back_populates="neighbourhood")
    zones   = relationship("GeospatialZone", back_populates="neighbourhood")
    retention_policies = relationship("RetentionPolicy", back_populates="neighbourhood")