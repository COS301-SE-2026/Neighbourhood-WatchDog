from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class CreateNeighbourhoodReq(BaseModel):
    name: str
    location: str
    property_id: UUID

class NeighbourhoodRes(BaseModel):
    id: UUID
    name: str
    location: str   
    join_code: str
    created_at: datetime

class CreateNeighbourhoodRes(BaseModel):     
    status: int
    message: str | None = None
    data: NeighbourhoodRes | None = None