from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional
from app.models.property import PropertyTypeEnum
from uuid import UUID
from datetime import datetime

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class CreatePropertyReq(BaseModel):
    address: NonEmptyString
    property_type: PropertyTypeEnum

class PropertyRes(BaseModel):
    property_id: UUID
    neighbourhood_id: UUID | None
    address: NonEmptyString
    property_type: PropertyTypeEnum
    created_at: datetime

class CreatePropertyRes(BaseModel):
    status: int
    message: str | None = None
    data: PropertyRes | None = None

class UserSummary(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]

class CameraSummary(BaseModel):
    id: UUID
    location: str
    visibility: str
    created_at: datetime

class NeighbourhoodSummary(BaseModel):
    id: UUID
    name: str
    location: str
    join_code: str
    created_at: datetime

class PropertyDetailedRes(BaseModel):
    property_id: UUID
    address: str
    property_type: PropertyTypeEnum
    created_at: datetime
    users: list[UserSummary]
    neighbourhood: Optional[NeighbourhoodSummary]
    cameras: list[CameraSummary]