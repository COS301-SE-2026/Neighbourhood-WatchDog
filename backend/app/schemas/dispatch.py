from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Literal

from app.models.dispatch import DispatchStatus
from app.models.security_officer import AvailabilityStatus

class DispatchCandidateRes(BaseModel):
    """One ranked candidate row for a given alert"""
    id: UUID
    alert_id: UUID
    officer_id: UUID | None
    rank: int | None
    score: float | None
    distance: float | None
    eta: float | None
    workload: int | None
    status: DispatchStatus
    officer_availability: AvailabilityStatus | None
    is_location_stale: bool
    created_at: datetime
    notified_at: datetime | None
    responded_at: datetime | None

class AlertDispatchRes(BaseModel):
    """Lists selected, pending and queued officers for a given alert"""
    alert_id: UUID
    selected: DispatchCandidateRes | None = None
    pending: list[DispatchCandidateRes] = [] #reserve queue ordered by rank
    queued: list[DispatchCandidateRes] = [] #busy officers
    no_candidate: bool = False

class RespondDispatchReq(BaseModel):
    action: Literal["ACCEPT", "DECLINE"]

class RespondDispatchRes(BaseModel):
    status: int
    message: str | None = None
    data: DispatchCandidateRes | None

class DispatchNotificationRes(BaseModel):
    """What a notified officer sees"""
    dispatch_id: UUID
    alert_id: UUID
    detection_type: str
    confidence_score: float
    thumbnail_url: str | None
    distance: float
    eta: float | None
    frame_timestamp: datetime
    notified_at: datetime
    expires_at: datetime | None = None #response deadline