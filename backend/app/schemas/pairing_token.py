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

class EdgeAgentsCredentials(BaseModel):
    property_id: UUID
    address: str # the street address of the property so the user can know that they are connected to the right address
    api_key: str
    created_at: datetime

class EdgeAgentsCredentials(BaseModel):
    status: int
    message: str | None = None
    data: EdgeAgentsCredentials | None = None