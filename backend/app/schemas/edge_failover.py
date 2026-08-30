from uuid import UUID
from pydantic import BaseModel


class FailoverCameraRes(BaseModel):
    id: UUID
    property_id:UUID
    enabled: bool
    rtsp_url: str
    publish_username: str
    publish_password: str


class FailoverCamerasRes(BaseModel):
    data: list[FailoverCameraRes]