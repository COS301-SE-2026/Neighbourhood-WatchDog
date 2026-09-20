import pytest
from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from app.models.alert import DetectionType
from app.models.dispatch import Dispatch, DispatchStatus
from app.models.neighbourhood_user import NeighbourhoodRole
from app.models.security_officer import AvailabilityStatus
from app.services.security_officer_service import STALE_LOCATION_THRESHOLD_SECONDS
from app.services.dispatch_service import (
    ACTIVE_DISPATCH_STATUS,
    CRITICAL_DETECTION_TYPES,
    OFFICER_AVG_SPEED,
    RANKING_WEIGHTS,
    ROUTE_CIRCUITRY_FACTOR,
    AlertContext,
    OfficerCandidate,
    RankingWeights,
    _build_alert_dispatch_res,
    _build_dispatch_rows,
    _fetch_neighbourhood_officers,
    _fetch_workloads,
    _load_alert_context,
    dispatch_alert,
    estimate_eta_seconds,
    filter_eligible,
    get_alert_dispatch_hanlder,
    rank_candidates,
)

ALERT_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()
OTHER_NEIGHBOURHOOD_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
FIXED_NOW = datetime(2026, 9, 20, 0, 0, tzinfo=timezone.utc)

AVAILABLE = AvailabilityStatus.AVAILABLE
BUSY = AvailabilityStatus.BUSY
UNAVAVILABLE = AvailabilityStatus.UNAVAILABLE