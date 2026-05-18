from pydantic import BaseModel, StringConstraints
from typing import Annotated
from app.models.property import PropertyTypeEnum, Property
from uuid import UUID
from datetime import datetime

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class CreatePropertyReq(BaseModel):
    address: NonEmptyString
    property_type: PropertyTypeEnum

class PropertyRes(BaseModel):
    user_id: UUID
    neighbourhood_id: UUID | None
    address: NonEmptyString
    property_type: PropertyTypeEnum
    created_at: datetime

class CreatePropertyRes(BaseModel):     
    status: int
    message: str | None = None
    data: PropertyRes | None = None