from pydantic import BaseModel
from app.models.property import PropertyTypeEnum, Property

class CreatePropertyReq(BaseModel):
    address: str
    property_type: PropertyTypeEnum
    
class CreatePropertyRes(BaseModel):
    status: int 
    message: str | None = None
    data: Property | None = None