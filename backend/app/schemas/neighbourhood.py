from pydantic import BaseModel, StringConstraints
from typing import Annotated
from uuid import UUID
from datetime import datetime

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