from pydantic import BaseModel
from app.models.property import PropertyTypeEnum, Property
from uuid import UUID
from datetime import datetime

class CreatePropertyReq(BaseModel):
    address: str
    property_type: PropertyTypeEnum
    
class PropertyRes(BaseModel):
    user_id: UUID
    neighbourhood_id: UUID | None
    address: str
    property_type: PropertyTypeEnum
    created_at: datetime

class CreatePropertyRes(BaseModel):     
    status: int
    message: str | None = None
    data: PropertyRes | None = None