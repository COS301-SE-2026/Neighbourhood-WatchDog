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
