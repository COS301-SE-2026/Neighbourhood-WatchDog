from enum import Enum

from sqlalchemy import Column, Index, TIMESTAMP, text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class JoinRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class NeighbourhoodJoinRequest(Base):
    __tablename__ = "neighbourhood_join_request"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(SAEnum(JoinRequestStatus, name="join_request_status"), nullable=False, server_default=JoinRequestStatus.PENDING.value)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)

    neighbourhood = relationship("Neighbourhood", back_populates="join_requests")
    property = relationship("Property")
    user = relationship("User", back_populates="join_requests")

    __table_args__ = (
        Index("ix_join_request_user_id", "user_id"),
        Index("ix_join_request_property_id", "property_id"),
        Index(
            "ix_join_request_neighbourhood_status",
            "neighbourhood_id",
            "status",
        ),
        Index(
            "ix_join_request_neighbourhood_created_at",
            "neighbourhood_id",
            "created_at",
        ),
        Index(
            "uq_join_request_property_neighbourhood_pending",
            "property_id",
            "neighbourhood_id",
            "status",
        )
    )
