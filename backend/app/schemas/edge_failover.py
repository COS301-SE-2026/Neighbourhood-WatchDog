from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class FailoverCameraRes(BaseModel):
    id: UUID
    property_id:UUID
    enabled: bool
    rtsp_url: str
    publish_username: str
    publish_password: str
    edge_agent_last_seen_at: datetime | None = None


class FailoverCamerasRes(BaseModel):
    data: list[FailoverCameraRes]