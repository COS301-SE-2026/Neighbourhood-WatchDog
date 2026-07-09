from pydantic import BaseModel
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

class CameraRes(BaseModel):
    id: UUID
    property_id: UUID
    neighbourhood_id: UUID
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
    data: list[CameraRes] = []


class CameraEditReq(BaseModel):
    name: NonEmptyString | None = None
    location: NonEmptyString | None = None
    visibility: CameraVisibilityEnum | None = None
    enabled: bool | None = None


class EditCameraRes(BaseModel):
    status: int
    message: NonEmptyString | None = None
    data: CameraRes | None = None