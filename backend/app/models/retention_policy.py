import uuid

from sqlalchemy import Column, ForeignKey, Integer, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from app.core.database import Base


class RetentionPolicy(Base):
    __tablename__ = "retention_policy"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id        = Column(UUID(as_uuid=True), ForeignKey("camera.id"), nullable=False, index=True)
    hot_seconds      = Column(Integer, nullable=False)
    warm_seconds     = Column(Integer, nullable=False)
    cold_seconds     = Column(Integer, nullable=False)
    created_at       = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at       = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=text("now()"))

    camera        = relationship("Camera", back_populates="retention_policy")

    __table_args__ = (
        CheckConstraint("hot_seconds > 0",  name="check_hot_seconds_positive"),
        CheckConstraint("warm_seconds > 0", name="check_warm_seconds_positive"),
        CheckConstraint("cold_seconds > 0", name="check_cold_seconds_positive"),
    )

    
    