from enum import Enum

from app.core.database import Base
from sqlalchemy import Column, ForeignKey, String, text, Enum as SAEnum, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID


class PropertyType(str, Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"


class Property(Base):
    __tablename__ = "property"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id"), nullable=False)
    address = Column(String, nullable=False)
    property_type = Column(SAEnum(PropertyType, name="property_type"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))