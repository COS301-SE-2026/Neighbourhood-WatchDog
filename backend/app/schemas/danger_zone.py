from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class DangerZoneQuery(BaseModel):
    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)

    @model_validator(mode="after")
    def validate_viewport(self):
        if self.west >= self.east:
            raise ValueError("west must be less than east")

        if self.south >= self.north:
            raise ValueError("south must be less than north")

        return self


class DangerZoneCellResponse(BaseModel):
    cell_id: str
    grid_x: int
    grid_y: int
    latitude: float
    longitude: float

    south: float
    west: float
    north: float
    east: float

    incident_count: int
    incident_score: float = Field(ge=0, le=1)
    coverage_ratio: float = Field(ge=0, le=1)
    coverage_sparsity: float = Field(ge=0, le=1)
    danger_score: float = Field(ge=0, le=1)


class DangerZoneData(BaseModel):
    neighbourhood_id: UUID
    window_start: date | None
    window_end: date | None
    calculated_at: datetime | None
    cell_size_metres: int = 100
    min_score: float = Field(ge=0, le=1)
    max_score: float = Field(ge=0, le=1)
    cells: list[DangerZoneCellResponse]


class DangerZoneResponse(BaseModel):
    status: int
    message: str | None = None
    data: DangerZoneData