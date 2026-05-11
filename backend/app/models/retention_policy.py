import uuid

from sqlalchemy import Column, ForeignKey, Integer, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
from sqlalchemy.orm import relationship
from app.core.database import Base


class RetentionPolicy(Base):
    __tablename__ = "retention_policy"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id"), nullable=True)
    camera_id        = Column(UUID(as_uuid=True), ForeignKey("camera.id"), nullable=True)
    hot_seconds      = Column(Integer, nullable=False)
    warm_seconds     = Column(Integer, nullable=False)
    cold_seconds     = Column(Integer, nullable=False)
    created_at       = Column(TIMESTAMPTZ, nullable=False, server_default=text("now()"))
    updated_at       = Column(TIMESTAMPTZ, nullable=False, server_default=text("now()"), onupdate=text("now()"))

    neighbourhood = relationship("Neighbourhood", back_populates="retention_policies")
    camera        = relationship("Camera", back_populates="retention_policy")

    __table_args__ = (
        CheckConstraint("hot_seconds > 0",  name="check_hot_seconds_positive"),
        CheckConstraint("warm_seconds > 0", name="check_warm_seconds_positive"),
        CheckConstraint("cold_seconds > 0", name="check_cold_seconds_positive"),
        CheckConstraint(
            "camera_id IS NOT NULL OR neighbourhood_id IS NOT NULL",
            name="check_at_least_one_scope"
        ),
    )

    
    