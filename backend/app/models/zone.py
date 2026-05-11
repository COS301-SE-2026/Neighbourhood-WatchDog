import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Column, ForeignKey, Text, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base
from models.enums import SensitivityLevel


class GeospatialZone(Base):
    __tablename__ = "geospatial_zone"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    polygon_boundary = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    sensitivity_level = Column(
        Enum(SensitivityLevel, name="sensitivity_level"),
        nullable=False,
        server_default=SensitivityLevel.MEDIUM.value
    )

    neighbourhood = relationship("Neighbourhood", back_populates="zones")