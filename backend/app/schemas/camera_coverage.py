from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.camera_coverage import MAX_CAMERA_COVERAGE_RANGE_METRES


class CameraCoverageInput(BaseModel):
    origin_latitude: float = Field(..., ge=-90, le=90)
    origin_longitude: float = Field(..., ge=-180, le=180)
    coverage_bearing_degrees: float = Field(..., ge=0, lt=360)
    coverage_angle_degrees: float = Field(..., ge=1, le=180)
    coverage_range_metres: float = Field(
        ...,
        ge=1,
        le=MAX_CAMERA_COVERAGE_RANGE_METRES,
    )


class CameraCoverageResponse(CameraCoverageInput):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    camera_id: UUID
    polygon: list[list[float]]