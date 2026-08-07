from enum import Enum
import uuid
from sqlalchemy import Column, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class NeighbourhoodRole(str, Enum):
    RESIDENT = "RESIDENT"
    NEIGHBOURHOOD_ADMIN = "NEIGHBOURHOOD_ADMIN"
    SECURITY_OFFICER = "SECURITY_OFFICER"

class NeighbourhoodUser(Base):
    __tablename__ = "neighbourhood_user"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=False)
    role = Column(SAEnum(NeighbourhoodRole, name="neighbourhood_role"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="neighbourhood_memberships")
    neighbourhood = relationship("Neighbourhood", back_populates="user_memberships")
    
    __table_args__ = (
        Index("uq_neighbourhood_user_unique", "user_id", "neighbourhood_id", unique=True),
        Index("ix_neighbourhood_user_user_lookup", "user_id"),
        Index("ix_neighbourhood_user_neighbourhood_role", "neighbourhood_id", "role"),
    )