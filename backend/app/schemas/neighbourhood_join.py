from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, StringConstraints, field_validator

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class JoinNeighbourhoodReq(BaseModel):
    join_code: NonEmptyString

class JoinRequestRes(BaseModel):
    id: UUID
    neighbourhood_id: UUID
    user_id: UUID
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class JoinNeighbourhoodRes(BaseModel):
    status: int
    message: str | None = None
    data: JoinRequestRes | None = None

class ResolveJoinRequestReq(BaseModel):
    action: str

    @field_validator("action")
    @classmethod
    def action_is_valid(cls, v: str) -> str:
        if v.upper() not in ("APPROVE", "DENY"):
            raise ValueError("Action must be APPROVE or DENY.")
        return v.upper()

class ResolveJoinRequestRes(BaseModel):
    status: int
    message: str | None = None
    data: JoinRequestRes | None = None
