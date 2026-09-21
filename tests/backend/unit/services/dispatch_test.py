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

    def test_empty_input(self):
         assert filter_eligible([]) == []

    def test_filtered_officers_keep_original_order(self):
        available_officers = make_candidate(availability_status=AVAILABLE)
        busy_officers = make_candidate(availability_status=BUSY)
        candidates = [
            make_candidate(availability_status=UNAVAILABLE),
            available_officers,
            make_candidate(age=STALE_LOCATION_THRESHOLD_SECONDS + 60),
            replace(make_candidate(), distance=None),
            busy_officers,
        ]

        assert filter_eligible(candidates) == [available_officers, busy_officers]

class TestEstimateEta:
    def test_zero_distance_is_zero_seconds(self):
        assert estimate_eta_seconds(0.0) == 0.0

    def test_uses_route_circuitry_and_avg_speed(self):
        expected = 1000.0 * ROUTE_CIRCUITRY_FACTOR / OFFICER_AVG_SPEED
        assert estimate_eta_seconds(1000.0) == pytest.approx(expected)

    def test_eta_increases_with_distance(self):
        assert estimate_eta_seconds(2000.0) > estimate_eta_seconds(1000.0)

    def test_eta_scales_linearly(self):
        assert estimate_eta_seconds(2000.0) == pytest.approx(2 * estimate_eta_seconds(1000.0))

@pytest.mark.usefixtures("fixed_weights")
class TestRankCandidates:
    def test_empty_input(self):
        assert rank_candidates([], "WEAPON_DETECTED", now=FIXED_NOW) == []

    def test_nearest_available_officer_ranks_first(self):
        far = make_candidate(distance=2000.0, now=FIXED_NOW)
        mid = make_candidate(distance=900.0, now=FIXED_NOW)
        near = make_candidate(distance=300.0, now=FIXED_NOW)

        ranked = rank_candidates([far, near, mid], "WEAPON_DETECTED", now=FIXED_NOW)

        assert [r.candidate.officer_id for r in ranked] == [
            near.officer_id,
            mid.officer_id,
            far.officer_id
        ]

    def test_ranks_start_at_one_and_are_consecutive(self):
        candidates = [make_candidate(distance=d, now=FIXED_NOW) for d in (100, 200, 300, 400)]
        ranked = rank_candidates(candidates, "WEAPON_DETECTED", now=FIXED_NOW)
        assert [r.rank for r in ranked] == [1, 2, 3, 4]

    def test_scores_increase_with_rank(self):
        candidates = [make_candidate(distance=d, now=FIXED_NOW) for d in (900, 100, 500)]
        ranked = rank_candidates(candidates, "WEAPON_DETECTED", now=FIXED_NOW)
        scores = [r.score for r in ranked]
        assert scores == sorted(scores)

    def test_available_officers_rank_ahead_of_busy_officers(self):
        busy_officer = make_candidate(availability_status=BUSY, distance=50.0, now=FIXED_NOW)
        available_officer = make_candidate(availability_status=AVAILABLE, distance=5000.0, now=FIXED_NOW)
        ranked = rank_candidates([busy_officer, available_officer], "WEAPON_DETECTED", now=FIXED_NOW)
        assert ranked[0].candidate.officer_id == available_officer.officer_id
        assert ranked[1].candidate.officer_id == busy_officer.officer_id
        assert ranked[1].score < ranked[0].score

    def test_busy_officers_are_ranked_by_score(self):
        far = make_candidate(availability_status=BUSY, distance=2000.0, now=FIXED_NOW)
        near = make_candidate(availability_status=BUSY, distance=200.0, now=FIXED_NOW)
        ranked = rank_candidates([far, near], "WEAPON_DETECTED", now=FIXED_NOW)
        assert ranked[0].candidate.officer_id == near.officer_id

    def test_higher_workload_ranks_lower_when_distance_equal(self):
        loaded = make_candidate(distance=500.0, workload=2, now=FIXED_NOW)
        idle = make_candidate(distance=500.0, workload=0, now=FIXED_NOW)
        ranked = rank_candidates([loaded, idle], "WEAPON_DETECTED", now=FIXED_NOW)
        assert ranked[0].candidate.officer_id == idle.officer_id

    def test_fresher_location_ranks_higher_when_everything_else_equal(self):
        stale = make_candidate(age=100, now=FIXED_NOW)
        fresh = make_candidate(age=5, now=FIXED_NOW)
        ranked = rank_candidates([stale, fresh], "WEAPON_DETECTED", now=FIXED_NOW)
        assert ranked[0].candidate.officer_id == fresh.officer_id
    
    def test_alert_type_changes_workload_distance_tradeoff(self):
        closer_but_loaded = make_candidate(distance=500.0, workload=1, now=FIXED_NOW)
        farther_but_idle = make_candidate(distance=600.0, workload=0, now=FIXED_NOW)
        candidates = [closer_but_loaded, farther_but_idle]
        weapon = rank_candidates(candidates, "WEAPON_DETECTED", now=FIXED_NOW)
        fall = rank_candidates(candidates, "FALL_DETECTED", now=FIXED_NOW)
        assert weapon[0].candidate.officer_id == closer_but_loaded.officer_id
        assert fall[0].candidate.officer_id == farther_but_idle.officer_id

    def test_unkown_detection_type_uses_default_weights(self):
        candidate = make_candidate(distance=600.0, workload=1, age=10, now=FIXED_NOW)
        unknown = rank_candidates([candidate], "SOMETHING_NEW", now=FIXED_NOW)
        expected = (
            1.0 * estimate_eta_seconds(600.0) / 60.0
            + 1.0 * 1
            + 0.5 * (10 / STALE_LOCATION_THRESHOLD_SECONDS)
        )
        assert unknown[0].score == pytest.approx(expected)

    def test_score_matches_formula(self):
        candidate = make_candidate(distance=1000.0, workload=2, age=60, now=FIXED_NOW)
        ranked = rank_candidates([candidate], "WEAPON_DETECTED", now=FIXED_NOW)
        eta = estimate_eta_seconds(1000.0)
        expected = 1.5 * (eta / 60.0) + 0.25 * 2 + 0.5 * (60 / STALE_LOCATION_THRESHOLD_SECONDS)
        assert ranked[0].eta == pytest.approx(eta)
        assert ranked[0].score == pytest.approx(expected)

    def test_freshness_is_capped_at_staleness_threshold(self):
        at_threshold = make_candidate(age=STALE_LOCATION_THRESHOLD_SECONDS, now=FIXED_NOW)
        past_threshold = make_candidate(age=STALE_LOCATION_THRESHOLD_SECONDS * 5, now=FIXED_NOW)
        a = rank_candidates([at_threshold], "WEAPON_DETECTED", now=FIXED_NOW)[0]
        b = rank_candidates([past_threshold], "WEAPON_DETECTED", now=FIXED_NOW)[0]
        assert a.score == pytest.approx(b.score)

    def test_future_location_timestamp_gets_no_freshness_penalty(self):
        skewed = make_candidate(age=-30, distance=1000.0, now=FIXED_NOW)
        ranked = rank_candidates([skewed], "WEAPON_DETECTED", now=FIXED_NOW)
        assert ranked[0].score == pytest.approx(1.5 * estimate_eta_seconds(1000.0) / 60.0)

    def test_ties_broken_by_officer_id(self):
        low = make_candidate(officer_id=UUID(int=1), now=FIXED_NOW)
        high = make_candidate(officer_id=UUID(int=2), now=FIXED_NOW)

        forwards = rank_candidates([low, high],"WEAPON_DETECTED", now=FIXED_NOW)
        backwards = rank_candidates([high, low],"WEAPON_DETECTED", now=FIXED_NOW)
        assert [r.candidate.officer_id for r in forwards] == [low.officer_id, high.officer_id]
        assert [r.candidate.officer_id for r in backwards] == [low.officer_id, high.officer_id]

    def test_ranking_does_not_change_or_drop_candidates(self):
        candidates = [make_candidate(distance=d, now=FIXED_NOW) for d in (300, 100, 200)]
        og = list(candidates)
        ranked = rank_candidates(candidates, "WEAPON_DETECTED", now=FIXED_NOW)
        assert candidates == og
        assert {r.candidate.officer_id for r in ranked} == {o.officer_id for o in og}

    def test_every_critical_detection_type_has_ranking_profile(self):
         assert CRITICAL_DETECTION_TYPES <= set(RANKING_WEIGHTS)

class TestBuildDispatchRows:
    def rank(self, *candidates):
         return rank_candidates(list(candidates), "WEAPON_DETECTED", now=FIXED_NOW)

    def test_nearest_officer_selected_and_others_pending(self):
        far = make_candidate(distance=3000.0, now=FIXED_NOW)
        mid = make_candidate(distance=800.0, now=FIXED_NOW)
        near = make_candidate(distance=200.0, now=FIXED_NOW)

        rows = _build_dispatch_rows(make_context(), self.rank(far, near, mid))

        assert [(r.officer_id, r.status) for r in rows] == [
            (near.officer_id, DispatchStatus.SELECTED),
            (mid.officer_id, DispatchStatus.PENDING),
            (far.officer_id, DispatchStatus.PENDING),
        ]

    def test_exactly_one_officer_is_selected(self):
        candidates = [make_candidate(distance=d, now=FIXED_NOW) for d in (100, 200, 300)]
        rows = _build_dispatch_rows(make_context(), self.rank(*candidates))
        assert sum(r.status == DispatchStatus.SELECTED for r in rows) == 1

    def test_busy_officers_are_queued(self):
        available = make_candidate(availability_status=AVAILABLE, distance=2000.0, now=FIXED_NOW)
        busy = make_candidate(availability_status=BUSY, distance=50.0, now=FIXED_NOW)
        rows = _build_dispatch_rows(make_context(), self.rank(available, busy))
        by_officer = {r.officer_id: r for r in rows}
        assert by_officer[available.officer_id].status == DispatchStatus.SELECTED
        assert by_officer[busy.officer_id].status == DispatchStatus.QUEUED

    def test_queued_officers_rank_after_available(self):
        available = [make_candidate(distance=d, now=FIXED_NOW) for d in (500, 900)]
        busy = make_candidate(availability_status=BUSY, distance=10.0, now=FIXED_NOW)
        rows = _build_dispatch_rows(make_context(), self.rank(*available, busy))
        assert [r.rank for r in rows] == [1, 2, 3]
        assert rows[-1].status == DispatchStatus.QUEUED

    def test_no_candidate_records_no_candidate_row(self):
        context = make_context()
        rows = _build_dispatch_rows(context, [])
        assert len(rows) == 1
        row = rows[0]
        assert row.status == DispatchStatus.NO_CANDIDATE
        assert row.officer_id is None
        assert row.rank is None
        assert row.alert_id == ALERT_ID
        assert row.neighbourhood_id == NEIGHBOURHOOD_ID

    def test_records_selected_officer_and_ranking_inputs(self):
        officer = make_candidate(distance=750.0, workload=1, age=20, now=FIXED_NOW)
        ranked = self.rank(officer)
        row = _build_dispatch_rows(make_context(), ranked)[0]
        assert row.alert_id == ALERT_ID
        assert row.neighbourhood_id == NEIGHBOURHOOD_ID
        assert row.officer_id == officer.officer_id
        assert row.status == DispatchStatus.SELECTED
        assert row.rank == 1
        assert row.score == pytest.approx(ranked[0].score)
        assert row.distance == 750.0
        assert row.eta == pytest.approx(ranked[0].eta)
        assert row.workload == 1
        assert row.officer_availability == AVAILABLE
        assert row.officer_location_updated_at == officer.location_updated_at

    def test_every_row_has_alerts_neighbourhood(self):
        candidates = [make_candidate(now=FIXED_NOW), make_candidate(now=FIXED_NOW)]
        rows = _build_dispatch_rows(make_context(), self.rank(*candidates))
        assert {r.neighbourhood_id for r in rows} == {NEIGHBOURHOOD_ID}