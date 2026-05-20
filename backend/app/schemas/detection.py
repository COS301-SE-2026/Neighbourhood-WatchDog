from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

class DetectionIngestReq(BaseModel):
    camera_id: UUID
    frame_timestamp: datetime
    detection_type: str
    confidence_score: float
    thumbnail_url: str | None = None
    zone_id: UUID | None = None

    @field_validator("confidence_score")
    @classmethod
    def score_must_be_valid(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")
        return v

    @field_validator("detection_type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        valid = {
            "HUMAN_PRESENCE",
            "LOITERING",
            "PERIMETER_SCAN",
            "WEAPON_DETECTED",
            "FALL_DETECTED",
        }
        if v not in valid:
            raise ValueError(f"detection_type must be one of {sorted(valid)}")
        return v

class DetectionEventRes(BaseModel):
    id: UUID
    camera_id: UUID
    frame_timestamp: datetime
    detection_type: str
    confidence_score: float
    thumbnail_url: str | None = None
    processed: bool

    model_config = {"from_attributes": True}

class DetectionIngestRes(BaseModel):
    status: int
    message: str | None = None
    data: DetectionEventRes | None = None
    alert_created: bool
    alert_id: UUID | None = None
