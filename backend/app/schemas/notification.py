from enum import Enum
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class NotificationRes(BaseModel):
    id: UUID
    alert_id: UUID
    user_id: UUID
    channel: str
    status: str
    sent_at: datetime

    model_config = {"from_attributes": True}

class ListNotificationRes(BaseModel):
    status: int
    message: Optional[str] = None
    data: list[NotificationRes] = []

class EventType(str, Enum):
    WEAPON_DETECTED = "WEAPON_DETECTED"
    NEIGHBOURHOOD_BROADCAST = "NEIGHBOURHOOD_BROADCAST"
    GENERAL_DETECTION = "GENERAL_DETECTION"
    TRACKING_MATCH = "TRACKING_MATCH"
    PROPERTY_INVITE = "PROPERTY_INVITE"
    JOIN_REQUEST = "JOIN_REQUEST"
    JOIN_REQUEST_RESOLVED = "JOIN_REQUEST_RESOLVED"