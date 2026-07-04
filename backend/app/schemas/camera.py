from pydantic import BaseModel, Field
from app.schemas.property import NonEmptyString
from app.models.camera import CameraVisibilityEnum
from uuid import UUID
from datetime import datetime

class RegisterCameraReq(BaseModel):
    rtsp_url: NonEmptyString
    location: NonEmptyString
    visibility: CameraVisibilityEnum
    property_id: UUID

class CameraRes(BaseModel):
    id: UUID
    property_id: UUID
    neighbourhood_id: UUID
    visibility: CameraVisibilityEnum
    location: NonEmptyString
    rtsp_url: NonEmptyString
    created_at: datetime

class RegisterCameraRes(BaseModel):
    status: int
    message: NonEmptyString | None = None
    data: CameraRes | None = None

class CamerasRes(BaseModel):
    status: int
    data: list[CameraRes] = []


class CameraEdit(BaseModel):
    camera_name: NonEmptyString | None = None
    location: NonEmptyString | None = None
    visibility: CameraVisibilityEnum | None = None
    enabled: bool | None = None


class EditCameraRes(BaseModel):
    status: int
    message: NonEmptyString | None = None
    data: CameraRes | None = None