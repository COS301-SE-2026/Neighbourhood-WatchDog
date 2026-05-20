from sqlalchemy import Column, String, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class NeighbourhoodJoinRequest(Base):
    __tablename__ = "neighbourhood_join_request"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False, server_default="PENDING")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)

    neighbourhood = relationship("Neighbourhood", back_populates="join_requests")
    user = relationship("User", back_populates="join_requests")
