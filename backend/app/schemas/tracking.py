
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class TrackingSightingResponse(BaseModel):
    id: UUID
    camera_id: UUID
    camera_name: str
    camera_location: str
    local_track_id: int
    observed_at: datetime
    sequence_no: int
    match_confidence: float | None = None


    model_config = ConfigDict(from_attributes=True)



class TrackingTimelineData(BaseModel):
    alert_id: UUID
    tracking_subject_id: UUID
    alert_status: str
    sightings: list[TrackingSightingResponse]


class TrackingTimelineResponse(BaseModel):
    status: int
    message: str | None = None
    data: TrackingTimelineData | None = None


#compare payload against existing subjects
class MatchTrackingEmbeddingRequest(BaseModel):
    camera_id: UUID

    appearance_embedding: list[float] = Field(
        min_length=1280,
        max_length=1280 

    )

    embedding_model: str = Field(
        min_length=1,
        max_length=128 

    )


class TrackingMatchData(BaseModel):
    matched: bool
    tracking_subject_id: UUID | None = None
    similarity: float | None = None
    threshold: float


class TrackingMatchResponse(BaseModel):
    status: int
    message: str
    data: TrackingMatchData