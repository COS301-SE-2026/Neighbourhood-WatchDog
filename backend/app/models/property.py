from enum import Enum

from app.core.database import Base
from sqlalchemy import Column, ForeignKey, String, text, Enum as SAEnum, TIMESTAMP, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class PropertyTypeEnum(str, Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"


class Property(Base):
    __tablename__ = "property"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=True, index=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable = True)
    longitude = Column(Float, nullable = True)
    property_type = Column(SAEnum(PropertyTypeEnum, name="property_type"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    neighbourhood = relationship("Neighbourhood", foreign_keys=[neighbourhood_id], back_populates="properties")
    cameras = relationship("Camera", back_populates="property", cascade="all, delete-orphan")
    edge_agent_credentials = relationship("EdgeAgentCredential", back_populates="property", cascade="all, delete-orphan")