from app.schemas.camera import CameraListItemRes

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class LinkPropertyToken(BaseModel):
    token: str
    expires_at: datetime

class LinkPropertyTokenRes(BaseModel):
    status: int
    message: str | None = None
    data: LinkPropertyToken | None = None

class EdgeAgentsCredentialsSchema(BaseModel):
    property_id: UUID
    address: str # the street address of the property so the user can know that they are connected to the right address
    api_key: str
    cameras: list[CameraListItemRes]
    created_at: datetime

class EdgeAgentsCredentialsRes(BaseModel):
    status: int
    message: str | None = None
    data: EdgeAgentsCredentialsSchema | None = None