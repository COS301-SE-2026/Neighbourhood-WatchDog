from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UpdateRiskThresholdConfigReq(BaseModel):
    low_max: float | None = None
    medium_max: float | None = None

class RiskThresholdConfigRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    neighbourhood_id : UUID
    low_max : float
    medium_max : float
    updated_at : datetime