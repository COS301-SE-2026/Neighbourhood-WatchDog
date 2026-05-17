from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class CreateNeighbourhoodReq(BaseModel):
    name: str
    location: str

class NeighbourhoodRes():
    id: UUID
    name: str
    location: str
    created_at: datetime

class CreatePropertyRes(BaseModel):     
    status: int
    message: str | None = None
    data: NeighbourhoodRes | None = None