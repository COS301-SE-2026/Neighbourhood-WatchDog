from app.core.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, text, CheckConstraint, Float, TIMESTAMP
from sqlalchemy.orm import relationship




class RiskThresholdConfig(Base):
    __tablename__ = "risk_threshold_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id"), nullable=True, index=True)
    low_max = Column(Float, nullable=False)
    medium_max = Column(Float, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=text("now()"))

    neighbourhood = relationship("Neighbourhood", back_populates="risk_thresholds")

    __table_args__ = (
        CheckConstraint('low_max >= 0', name="check_low_max_non_negative"),
        CheckConstraint('medium_max >= 0', name="check_medium_max_non_negative"),
        CheckConstraint('medium_max > low_max', name="check_medium_max_greater_than_low_max")
    )


