from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.dispatch import DispatchStatus
from app.models.security_officer import AvailabilityStatus
from app.schemas.dispatch import AlertDispatchRes, DispatchCandidateRes, DispatchNotificationRes, RespondDispatchReq, RespondDispatchRes

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

def make_candidate(**overrides):
    kwargs = dict(
        id=uuid4(),
        alert_id=uuid4(),
        officer_id=uuid4(),
        rank=1,
        score=2.5,
        distance=800.0,
        eta=120.0,
        workload=0,
        status=DispatchStatus.SELECTED,
        officer_availability=AvailabilityStatus.AVAILABLE,
        is_location_stale=False,
        created_at=NOW,
        notified_at=None,
        responded_at=None,
    )
    kwargs.update(overrides)
    return kwargs