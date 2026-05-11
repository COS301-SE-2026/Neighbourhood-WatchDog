import uuid

from sqlalchemy import Column, Text, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
from sqlalchemy.orm import relationship
from app.core.database import Base

class Neighbourhood(Base):
    __tablename__ = "neighbourhood"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    location = Column(Text, nullable=False)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=text("now()"))

    users   = relationship("User", back_populates="neighbourhood")
    cameras = relationship("Camera", back_populates="neighbourhood")
    zones   = relationship("Zone", back_populates="neighbourhood")