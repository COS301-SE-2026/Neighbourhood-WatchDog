from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator
from typing_extensions import Self


class UpdateRiskThresholdConfigReq(BaseModel):
    low_max: float | None = None
    medium_max: float | None = None

    @model_validator(mode="after")
    def validate_empty_req(self) -> Self:
        if self.low_max is None and self.medium_max is None:
            raise ValueError("At least one of low_max or medium_max must be provided")
        return self

class RiskThresholdConfigRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    neighbourhood_id : UUID | None
    low_max : float
    medium_max : float
    updated_at : datetime

class NeighbourhoodRiskThresholdConfigRes(BaseModel):
    status: int
    message: str
    data: RiskThresholdConfigRes