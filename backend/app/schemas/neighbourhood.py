from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    model_validator,
)
from typing import Annotated, Literal
from uuid import UUID
from enum import Enum
from datetime import datetime

from app.models.security_officer import AvailabilityStatus
from app.models.neighbourhood_user import NeighbourhoodRole
from math import isfinite

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

class NeighbourhoodMapPropertyRes(BaseModel):
    id: UUID
    address: NonEmptyString
    property_type: Literal["PRIVATE", "PUBLIC"]
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


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
    new_duty_status: OnDutyStatus

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


class NeighbourhoodBoundaryPolygon(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[tuple[float, float]]] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_polygon(self):
        for ring in self.coordinates:
            if len(ring) < 4:
                raise ValueError(
                    "Each polygon ring must contain at least four points"
                )

            if ring[0] != ring[-1]:
                raise ValueError(
                    "The polygon ring must be closed"
                )

            for longitude, latitude in ring:
                if not isfinite(longitude):
                    raise ValueError(
                        "Longitude must be finite"
                    )

                if not isfinite(latitude):
                    raise ValueError(
                        "Latitude must be finite"
                    )

                if not -180 <= longitude <= 180:
                    raise ValueError(
                        "Longitude must be between -180 and 180"
                    )

                if not -90 <= latitude <= 90:
                    raise ValueError(
                        "Latitude must be between -90 and 90"
                    )

        return self


class NeighbourhoodBoundaryImportReq(
    NeighbourhoodBoundaryPolygon,
):
    pass


class NeighbourhoodBoundaryData(BaseModel):
    neighbourhood_id: UUID
    geometry: NeighbourhoodBoundaryPolygon


class NeighbourhoodBoundaryRes(BaseModel):
    status: int
    message: str | None = None
    data: NeighbourhoodBoundaryData | None = None