from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class AlertCreate(BaseModel):
    track_id: int
    alert_type: str = "human_presence"
    confidence: float
    camera_id: str
    timestamp: datetime
    bbox: list[float] = []  # [x, y, w, h]


class AlertResponse(BaseModel):
    id: UUID
    track_id: int
    alert_type: str
    confidence: float
    camera_id: str
    timestamp: datetime
    bbox: list[float]
    created_at: datetime

    class Config:
        from_attributes = True