from pydantic import BaseModel
from app.models.property import PropertyTypeEnum, Property

class CreatePropertyReq(BaseModel):
    address: str
    propertyType: PropertyTypeEnum
    

class CreatePropertyRes(BaseModel):
    status: str 
    message: str | None = None
    data: Property | None = None