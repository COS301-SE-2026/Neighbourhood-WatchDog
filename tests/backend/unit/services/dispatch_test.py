import pytest
from dataclasses import replace
from datetime import datetime, timezone, timedelta
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

def make_mock_db():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = Mock()
    mock_db.add_all = Mock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.refresh = AsyncMock()
    return mock_db, mock_result

def make_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    result.scalar_one.return_value = value
    result.scalars.return_value.first.return_value = value
    result.scalars.return_value.all.return_value = [] if value is None else [value]
    return result

def make_rows_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result

def make_first_result(row):
    result = MagicMock()
    result.first.return_value = row
    return result

def make_scalars_result(rows):
    result = MagicMock()
    result.scalars.return_value.all.return_value = list(rows)
    return result

def compiled_params(stmt):
    return stmt.compile(dialect=postgresql.dialect()).params

def compiled_sql(stmt):
    return str(stmt.compile(dialect=postgresql.dialect()))

def make_candidate(
    *,
    officer_id=None,
    availability_status=AVAILABLE,
    distance=500.0,
    age=10,
    workload=0,
    now=None,
):
    now = now or datetime.now(timezone.utc)
    return OfficerCandidate(
        officer_id=officer_id or uuid4(),
        availability_status=availability_status,
        location_updated_at=now - timedelta(seconds=age),
        distance=distance,
        workload=workload,
    )

def make_context(**overrides):
    context = AlertContext(
        alert_id=ALERT_ID,
        detection_type="WEAPON_DETECTED",
        neighbourhood_id=NEIGHBOURHOOD_ID,
        latitude=-26.2041,
        longitude=28.0473,
    )
    return replace(context, **overrides)

def make_dispatch_row(
    status,
    *,
    officer_id=None,
    rank=None,
    updated_at=None,
    **overrides,
):
    kwargs = dict(
        id=uuid4(),
        alert_id=ALERT_ID,
        neighbourhood_id=NEIGHBOURHOOD_ID,
        officer_id=officer_id,
        rank=rank,
        score=1.0 if officer_id else None,
        distance=500.0 if officer_id else None,
        eta=78.0 if officer_id else None,
        workload=0 if officer_id else None,
        officer_availability=AVAILABLE if officer_id else None,
        officer_location_updated_at=updated_at,
        status=status,
        created_at=CREATED_AT,
    )
    kwargs.update(overrides)
    return Dispatch(**kwargs)