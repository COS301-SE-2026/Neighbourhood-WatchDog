
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


#payload for when a service reports a new sighting of a tracked subject
class RecordTrackingSightingRequest(BaseModel):
    tracking_subject_id: UUID
    camera_id: UUID
    local_track_id: int = Field(ge=0)
    observed_at: datetime
    match_confidence: float = Field(ge=0.0, le=1.0)


class TrackingSightingCreateData(BaseModel):
    alert_id: UUID
    tracking_subject_id: UUID
    sighting_id: UUID
    camera_id: UUID
    sequence_no: int
    match_confidence: float


class TrackingSightingCreateResponse(BaseModel):
    status: int
    message: str
    data: TrackingSightingCreateData



##situational briefing
class SituationalBriefCamera(BaseModel):
    camera_id: UUID
    camera_name: str
    camera_location: str
    property_id: UUID


class SituationalBriefAlert(BaseModel):
    alert_id: UUID
    detection_type: str
    confidence_score: float
    status: str
    observed_at: datetime
    camera_id: UUID
    camera_name: str
    camera_location: str


class SituationalBriefSighting(BaseModel):
    sighting_id: UUID
    sequence_no: int
    camera_id: UUID
    camera_name: str
    camera_location: str
    property_id: UUID
    local_track_id: int
    observed_at: datetime
    match_confidence: float | None = None


class SituationalBriefLastKnownLocation(BaseModel):
    camera_id: UUID
    camera_name: str
    camera_location: str
    property_id: UUID
    observed_at: datetime


class SituationalBriefData(BaseModel):
    tracking_subject_id: UUID
    generated_at: datetime
    trigger: str
    summary: str
    cameras: list[SituationalBriefCamera]
    alerts: list[SituationalBriefAlert]
    sightings: list[SituationalBriefSighting]
    last_known_location: list[SituationalBriefLastKnownLocation]


class SituationalBriefResponse(BaseModel):
    status: int
    message: str | None = None
    data: SituationalBriefData | None = None