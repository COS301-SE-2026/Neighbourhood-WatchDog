from pydantic import BaseModel, ConfigDict, Field
from app.schemas.property import NonEmptyString
from app.models.camera import CameraVisibilityEnum
from uuid import UUID
from datetime import datetime

class RegisterCameraReq(BaseModel):
    name: NonEmptyString
    rtsp_url: NonEmptyString
    location: NonEmptyString
    visibility: CameraVisibilityEnum
    property_id: UUID

class CameraListItemRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_id: UUID
    neighbourhood_id: UUID | None = None
    name: NonEmptyString
    visibility: CameraVisibilityEnum
    location: NonEmptyString
    enabled: bool
    created_at: datetime
    edge_agent_available: bool | None = None


class CameraRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    property_id: UUID
    neighbourhood_id: UUID | None = None
    name: NonEmptyString
    visibility: CameraVisibilityEnum
    location: NonEmptyString
    rtsp_url: NonEmptyString
    enabled: bool
    created_at: datetime

class RegisterCameraRes(BaseModel):
    status: int
    message: NonEmptyString | None = None
    data: CameraRes | None = None

class CamerasRes(BaseModel):
    status: int
    data: list[CameraListItemRes] = []


class CameraEditReq(BaseModel):
    name: NonEmptyString | None = None
    location: NonEmptyString | None = None
    visibility: CameraVisibilityEnum | None = None
    enabled: bool | None = None


class EditCameraRes(BaseModel):
    status: int
    message: NonEmptyString | None = None
    data: CameraRes | None = None

class EnabledCamerasRes(BaseModel):
    id: UUID
    rtsp_url: NonEmptyString
    enabled: bool
    neighbourhood_id: UUID | None = None
    confidence_threshold: float
    zones: list[list[list[float]]] = Field(default_factory=list)
    publish_username: NonEmptyString
    publish_password: NonEmptyString

class ListEnabledCameras(BaseModel):
    data: list[EnabledCamerasRes]

class MediaMtxAuthRequest(BaseModel):
    user: str = ""
    password: str = ""
    action: str = ""
    path: str = ""
    protocol: str = ""
    ip: str = ""
    id: str = ""
    query: str = ""

