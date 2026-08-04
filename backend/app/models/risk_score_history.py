from app.core.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey, Integer, text, CheckConstraint, Float, Enum as SAEnum, TIMESTAMP, Index
from enum import Enum
from sqlalchemy.orm import relationship


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class RiskScoreHistory(Base):
    __tablename__ = "risk_score_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)
    classification = Column(SAEnum(RiskLevel, name="risk_level"), nullable=False)
    alert_count = Column(Integer, default=0, nullable=False)
    calculated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=text("now()"))

    neighbourhood = relationship("Neighbourhood", back_populates="risk_scores", passive_deletes=True)

    __table_args__ = (
        CheckConstraint('alert_count >= 0', name="check_alert_count_non_negative"),
        CheckConstraint('score >= 0.0', name="check_score_non_negative"),
        Index("ix_risk_score_history_neighbourhood_calculated_at", "neighbourhood_id", "calculated_at"),
    )


