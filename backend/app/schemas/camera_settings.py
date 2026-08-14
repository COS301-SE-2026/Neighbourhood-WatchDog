from uuid import UUID
from typing import Annotated, List, Optional
from pydantic import BaseModel, ConfigDict, Field



Coordinate = Annotated[float, Field(ge=0.0, le=1.0)]
PolygonPoint = Annotated[List[Coordinate], Field(min_length=2, max_length=2)]

# class ZonePoint(BaseModel):
#     x: float = Field(..., ge=0.0, le=1.0)
#     y: float = Field(..., ge=0.0, le=1.0)



class CreateZoneRequest(BaseModel):
    name: str = Field(default="Zone", min_length=1, max_length=100)
    polygon: Annotated[List[PolygonPoint], Field(min_length=3)]




class ZoneResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    camera_id: UUID
    name: str
    polygon: List[List[float]]





class UpdateCameraSettingsRequest(BaseModel):
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    


class CameraSettingsResponse(BaseModel):
    camera_id: UUID
    confidence_threshold: float
    zones: List[ZoneResponse]

class UpdateCameraSettingsResponse(BaseModel):
    camera_id: UUID
    confidence_threshold: float
    