from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

from app.models.neighbourhood_user import NeighbourhoodRole
from app.models.user import UserRole

class GetUserResSchema(BaseModel):
    id: UUID
    email: str
    cognito_sub: str
    role: UserRole
    created_at: datetime

class CurrentUserSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: str | None = None
    system_role: UserRole


class CurrentUserNeighbourhood(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: str
    role: NeighbourhoodRole


class CurrentUserProperty(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    address: str
    neighbourhood_id: UUID | None
    is_admin: bool


class CurrentUserContextRes(BaseModel):
    user: CurrentUserSummary
    neighbourhoods: list[CurrentUserNeighbourhood]
    properties: list[CurrentUserProperty]