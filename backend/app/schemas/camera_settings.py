from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field


class ZonePoint(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)



class CreateZoneRequest(BaseModel):
    name: str = "Zone"
    polygon: List[List[float]] #like [[x, y], ...]



class ZoneResponse(BaseModel):
    id: UUID
    camera_id: UUID
    name: str
    polygon: List[List[float]]


    class Config:
        from_attributes = True



class UpdateCameraSettingsRequest(BaseModel):
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    


class CameraSettingsResponse(BaseModel):
    camera_id: UUID
    confidence_threshold: float
    zones: List[ZoneResponse]

    