from pydantic import BaseModel, StringConstraints, Field
from typing import Annotated
from app.models.property import PropertyTypeEnum
from uuid import UUID
from datetime import datetime

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class CreatePropertyReq(BaseModel):
    address: NonEmptyString
    property_type: PropertyTypeEnum
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

class PropertyRes(BaseModel):
    property_id: UUID
    neighbourhood_id: UUID | None
    address: NonEmptyString
    property_type: PropertyTypeEnum
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    created_at: datetime

class PropertyMember(BaseModel):
    user_id: UUID
    first_name: str | None = None
    last_name: str | None = None
    email: str

class PropertyMembers(BaseModel):
    members: list[PropertyMember] = Field(default_factory=list)

class CreatePropertyRes(BaseModel):
    status: int
    message: str | None = None
    data: PropertyRes | None = None

class UserSummary(BaseModel):
    id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None

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
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    created_at: datetime
    users: list[UserSummary]
    neighbourhood: NeighbourhoodSummary | None = None
    cameras: list[CameraSummary]