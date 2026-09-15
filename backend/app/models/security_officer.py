import uuid
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Index, DateTime
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from app.core.database import Base

class AvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"     # officer is ready to receive alerts
    BUSY = "BUSY"               # officer is busy with an incident but an alert can be added to the queue
    UNAVAILABLE = "UNAVAILABLE" # officer cannot receive alerts right now  

class SecurityOfficer(Base):
    """This table was added to add the availability_status attribute to the security 
        officer, while not having it in a table that contains other types of users
        as well. This is to maintain the Normalised nature of the schema"""
    __tablename__ = "security_officer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neighbourhood_user_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood_user.id", ondelete="CASCADE"), nullable=False, unique=True)
    availability_status = Column(SAEnum(AvailabilityStatus, name="availability_status"), nullable=True, default=AvailabilityStatus.UNAVAILABLE) # this is for security officers
    last_known_location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    location_updated_at = Column(DateTime(timezone=True), nullable=True)
    # Relationships
    neighbourhood_user = relationship("NeighbourhoodUser", back_populates="security_officer")

    __table_args__ = (
        Index("ix_security_officer_lookup", "neighbourhood_user_id", "availability_status"),
    )