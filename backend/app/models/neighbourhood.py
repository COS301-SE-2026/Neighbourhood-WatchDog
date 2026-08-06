import uuid

from sqlalchemy import Column, Text, text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.neighbourhood_user import NeighbourhoodUser 

class Neighbourhood(Base):
    __tablename__ = "neighbourhood"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    location = Column(Text, nullable=False)
    join_code = Column(Text, unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    properties = relationship("Property", back_populates="neighbourhood")
    zones   = relationship("GeospatialZone", back_populates="neighbourhood")
    risk_scores = relationship(
        "RiskScoreHistory", 
        back_populates="neighbourhood",
        cascade="all, delete-orphan",
        passive_deletes=True,)
    risk_thresholds = relationship(
        "RiskThresholdConfig", 
        back_populates="neighbourhood",
        cascade="all, delete-orphan",
        passive_deletes=True,)
    join_requests = relationship(
        "NeighbourhoodJoinRequest",
        back_populates="neighbourhood",
        cascade="all, delete-orphan",
    )
    user_memberships = relationship("NeighbourhoodUser", back_populates="neighbourhood", cascade="delete")
    
    
