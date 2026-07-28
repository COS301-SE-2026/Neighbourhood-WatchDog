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
