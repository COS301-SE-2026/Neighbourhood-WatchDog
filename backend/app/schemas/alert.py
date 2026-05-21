from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class AlertCreate(BaseModel):
    camera_id: UUID
    detection_type: str = "HUMAN_PRESENCE"
    confidence: float
    timestamp: datetime
    thumbnail_url: Optional[str] = None


class AlertResponse(BaseModel):
    id: UUID
    camera_id: UUID
    detection_event_id: UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True