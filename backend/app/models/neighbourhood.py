import uuid

from sqlalchemy import Column, Text, text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Neighbourhood(Base):
    __tablename__ = "neighbourhood"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    location = Column(Text, nullable=False)
    join_code = Column(Text, unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    users   = relationship("User", back_populates="neighbourhood")
    cameras = relationship("Camera", back_populates="neighbourhood")
    zones   = relationship("GeospatialZone", back_populates="neighbourhood")
    join_requests = relationship(
        "NeighbourhoodJoinRequest",
        back_populates="neighbourhood",
        cascade="all, delete-orphan",
    )
    retention_policies = relationship(
        "RetentionPolicy",
        back_populates="neighbourhood",
        cascade="all, delete-orphan",
    )
    
    