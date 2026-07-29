from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.models.risk_score_history import RiskLevel

class RiskScoreRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    neighbourhood_id: UUID
    score: float
    classification: RiskLevel
    alert_count: int
    calculated_at: datetime

class NeighbourhoodRiskScoreRes(BaseModel):
    status: int
    message: str
    data: RiskScoreRes | None = None

class NeighbourhoodRiskScoreHistoryRes(BaseModel):
    status: int
    message: str
    data: list[RiskScoreRes] = []