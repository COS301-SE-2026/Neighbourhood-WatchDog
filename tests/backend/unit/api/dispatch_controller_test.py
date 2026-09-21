from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.dispatch import get_alert_dispatch, router
from app.models.dispatch import DispatchStatus
from app.models.security_officer import AvailabilityStatus
from app.schemas.dispatch import AlertDispatchRes, DispatchCandidateRes

ALERT_ID = uuid4()
OFFICER_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
DB = Mock()
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)

def make_dispatch_res():
    selected = DispatchCandidateRes(
        id=uuid4(),
        alert_id=ALERT_ID,
        officer_id=OFFICER_ID,
        rank=1,
        score=2.5,
        distance=800.0,
        eta=120.0,
        workload=0,
        status=DispatchStatus.SELECTED,
        officer_availability=AvailabilityStatus.AVAILABLE,
        is_location_stale=False,
        created_at=CREATED_AT,
        notified_at=None,
        responded_at=None,
    )
    return AlertDispatchRes(alert_id=ALERT_ID, selected=selected)