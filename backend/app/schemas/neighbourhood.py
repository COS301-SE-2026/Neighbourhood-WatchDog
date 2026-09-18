from pydantic import BaseModel, StringConstraints, Field
from typing import Annotated, Literal
from uuid import UUID
from enum import Enum
from datetime import datetime

from app.models.security_officer import AvailabilityStatus
from app.models.neighbourhood_user import NeighbourhoodRole

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class CreateNeighbourhoodReq(BaseModel):
    name: NonEmptyString
    location: NonEmptyString
    property_id: UUID

class NeighbourhoodRes(BaseModel):
    id: UUID
    name: NonEmptyString
    location: NonEmptyString   
    join_code: NonEmptyString
    created_at: datetime

class CreateNeighbourhoodRes(BaseModel):     
    status: int
    message: str | None = None
    data: NeighbourhoodRes | None = None

class NeighbourhoodPropertyRes(BaseModel):
    id: UUID
    address: NonEmptyString
    property_type: Literal["PRIVATE", "PUBLIC"]
    neighbourhood_id: UUID | None = None
    neighbourhood_name: str | None = None


class UpdateMemberRoleReq(BaseModel):
    role: NeighbourhoodRole


class NeighbourhoodMemberRes(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    email: str
    role: NeighbourhoodRole


class UpdateMemberRoleRes(BaseModel):
    status: int
    message: str
    data: NeighbourhoodMemberRes


class GetSecurityAvailabilityRes(BaseModel):
    status: int
    message: str | None = None
    availability: AvailabilityStatus | None
    location_updated_at: datetime | None

class OnDutyStatus(str, Enum):
    ON_DUTY = "ON_DUTY"
    OFF_DUTY = "OFF_DUTY"

class UpdateSecurityAvailabilityReq(BaseModel):
    neighbourhood_id: UUID
    new_availability: OnDutyStatus

class UpdateSecurityAvailabilityRes(BaseModel):
    status: int
    message: str | None = None

class UpdateOfficerLocationReq(BaseModel):
    neighbourhood_id: UUID
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class UpdateOfficerLocationRes(BaseModel):
    status: int
    message: str | None = None

class OfficerLocationRes(BaseModel):
    officer_id: UUID
    latitude: float
    longitude: float
    location_updated_at: datetime
    is_stale: bool
    