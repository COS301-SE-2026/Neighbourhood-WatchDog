import pytest
from dataclasses import replace
from types import SimpleNamespace
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
UNAVAILABLE = AvailabilityStatus.UNAVAILABLE

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

def make_alert_row(context):
    return (
        context.alert_id,
        context.detection_type,
        context.neighbourhood_id,
        context.latitude,
        context.longitude,
    )

def make_officer_row(candidate):
    return (
        candidate.officer_id,
        candidate.availability_status,
        candidate.location_updated_at,
        candidate.distance,
    )

@pytest.fixture
def fixed_weights():
    with patch.dict(
        RANKING_WEIGHTS,
        {
            "WEAPON_DETECTED": RankingWeights(1.5, 0.25, 0.5),
            "FALL_DETECTED": RankingWeights(1.5, 0.5, 0.5),
        },
    ), patch("app.services.dispatch_service.DEFAULT_WEIGHTS", RankingWeights(1.0, 1.0, 0.5)):
        yield

def dispatch_steps(
   context,
   *,
   existing=(),
   officers=None,
   workloads=None,     
):
    steps = [make_first_result(make_alert_row(context)), make_scalars_result(existing)]
    if officers is not None:
        steps.append(make_rows_result([make_officer_row(o) for o in officers]))
    if workloads is not None:
        steps.append(make_rows_result(list(workloads.items())))
    return steps

async def run_dispatch(steps, mock_db=None, commit_error=None, refetch=None):
    if mock_db is None:
        mock_db, _ = make_mock_db()

    added: list[Dispatch] = []

    def add_all(rows):
        for row in rows:
            row.id = uuid4()
            row.created_at = CREATED_AT
        added.extend(rows)
    
    mock_db.add_all = Mock(side_effect=add_all)
    if commit_error is not None:
        mock_db.commit = AsyncMock(side_effect=commit_error)

    pending = list(steps)

    async def fake_execute(_stmt):
        if pending:
            return pending.pop(0)
        return make_scalars_result(added if refetch is None else refetch)

    mock_db.execute = AsyncMock(side_effect=fake_execute)

    res = await dispatch_alert(mock_db, ALERT_ID)

    assert not pending, "db.execute results were provided that dispatch_alert never asked for"
    return SimpleNamespace(res=res, db=mock_db, added=added)

class TestFilterEligible:
    def test_keeps_fresh_available_officer(self):
        officer = make_candidate(availability_status=AVAILABLE)
        assert filter_eligible([officer]) == [officer]

    def test_keeps_fresh_busy_officer_for_queuing(self):
            officer = make_candidate(availability_status=BUSY)
            assert filter_eligible([officer]) == [officer]

    def test_excludes_unavailable_officer(self):
            officer = make_candidate(availability_status=UNAVAILABLE)
            assert filter_eligible([officer]) == []

    def test_excludes_officer_without_availability(self):
            officer = make_candidate(availability_status=None)
            assert filter_eligible([officer]) == []

    def test_excludes_officer_with_stale_location(self):
            officer = make_candidate(age=STALE_LOCATION_THRESHOLD_SECONDS + 30)
            assert filter_eligible([officer]) == []

    def test_keeps_officer_within_stale_location_threshold(self):
            officer = make_candidate(age=STALE_LOCATION_THRESHOLD_SECONDS - 30)
            assert filter_eligible([officer]) == [officer]

    def test_excludes_officer_without_location_timestamp(self):
            officer = replace(make_candidate(), location_updated_at=None)
            assert filter_eligible([officer]) == []

    def test_excludes_officer_without_location(self):
            officer = replace(make_candidate(), distance=None)
            assert filter_eligible([officer]) == []