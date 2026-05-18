from pydantic import BaseModel
from app.schemas.property import NonEmptyString
from app.models.camera import CameraVisibilityEnum
from uuid import uuid4
from datetime import datetime

class RegisterCameraReq(BaseModel):
    rtsp_url: NonEmptyString
    property_id: uuid4

class CameraRes(BaseModel):
    property_id: uuid4
    neighbourhood_id: uuid4
    visibility: CameraVisibilityEnum
    location: NonEmptyString
    rtsp_url: NonEmptyString
    created_at: datetime

class RegisterCameraRes(BaseModel):
    status: int
    message: NonEmptyString | None = None
    data: CameraRes | None = None