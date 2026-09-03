from pydantic import BaseModel, StringConstraints
from typing import Annotated, Literal
from uuid import UUID
from datetime import datetime

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