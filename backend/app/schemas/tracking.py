
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

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
