import pytest
from dataclasses import replace
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.models.alert import DetectionType
from app.models.dispatch import Dispatch, DispatchStatus
from app.models.neighbourhood_user import NeighbourhoodRole
from app.models.security_officer import AvailabilityStatus
from app.services.neighbourhood_service import STALE_LOCATION_THRESHOLD_SECONDS
from app.services.dispatch_service import (
    ACTIVE_DISPATCH_STATUS,
    CRITICAL_DETECTION_TYPES,
    OFFICER_AVG_SPEED,
    RANKING_WEIGHTS,
    ROUTE_CIRCUITRY_FACTOR,
    RESPONSE_TIMEOUT,
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
    get_alert_dispatch_handler,
    rank_candidates,
    respond_to_dispatch_handler,
    expire_stale_dispatchs,
    _promote_officer,
    _escalate_dispatch,
    _expire_stale_dispatch,
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
    fallback_calls = 0

    async def fake_execute(_stmt):
        nonlocal fallback_calls
        if pending:
            return pending.pop(0)
        rows = added if refetch is None else refetch
        fallback_calls += 1
        result = make_scalars_result(rows)
        target_status = DispatchStatus.SELECTED if fallback_calls == 1 else DispatchStatus.NO_CANDIDATE
        result.scalar_one_or_none.return_value = next(
            (r for r in rows if r.status == target_status), None
        )
        return result

    mock_db.execute = AsyncMock(side_effect=fake_execute)

    with (
        patch("app.services.dispatch_service._notify_officer", new=AsyncMock()) as notify, 
        patch("app.services.dispatch_service._escalate_dispatch", new=AsyncMock()) as escalate,
    ):
        res = await dispatch_alert(mock_db, ALERT_ID)

    assert not pending, "db.execute results were provided that dispatch_alert never asked for"
    return SimpleNamespace(res=res, db=mock_db, added=added, notify=notify, escalate=escalate)

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

class TestBuildAlertDispatchRes:
    def test_no_rows_gives_empty_dispatch(self):
        res = _build_alert_dispatch_res(ALERT_ID, [])
        assert res.alert_id == ALERT_ID
        assert res.selected is None
        assert res.pending == []
        assert res.queued == []
        assert res.no_candidate is False

    def test_rows_split_into_categories(self):
        selected, pending, queued = uuid4(), uuid4(), uuid4()
        rows = [
            make_dispatch_row(DispatchStatus.SELECTED, officer_id=selected, rank=1),
            make_dispatch_row(DispatchStatus.PENDING, officer_id=pending, rank=2),
            make_dispatch_row(DispatchStatus.QUEUED, officer_id=queued, rank=3),
        ]
        res = _build_alert_dispatch_res(ALERT_ID, rows)

        assert res.selected.officer_id == selected
        assert [c.officer_id for c in res.pending] == [pending]
        assert [c.officer_id for c in res.queued] == [queued]
        assert res.no_candidate is False

    def test_active_statuses_count_as_selected(self):
        for status in (DispatchStatus.SELECTED, DispatchStatus.NOTIFIED, DispatchStatus.ACCEPTED):
            officer = uuid4()

            res = _build_alert_dispatch_res(
                ALERT_ID, [make_dispatch_row(status, officer_id=officer, rank=1)]
            )

            assert res.selected is not None
            assert res.selected.officer_id == officer
            assert res.selected.status == status

    def test_declined_and_timed_out_not_shown(self):
        for status in (DispatchStatus.DECLINED, DispatchStatus.TIMED_OUT):
            officer = uuid4()

            res = _build_alert_dispatch_res(
                ALERT_ID, [make_dispatch_row(status, officer_id=officer, rank=1)]
            )

            assert res.selected is None
            assert res.pending == []
            assert res.queued == []

    def test_no_candidate_sets_flag(self):
        res = _build_alert_dispatch_res(
            ALERT_ID, [make_dispatch_row(DispatchStatus.NO_CANDIDATE)]
        )

        assert res.no_candidate is True
        assert res.selected is None
        assert res.pending == []
        assert res.queued == []

    def test_is_location_stale_reflects_recorded_location_timestamp(self):
        now = datetime.now(timezone.utc)
        fresh = make_dispatch_row(
            DispatchStatus.SELECTED, officer_id=uuid4(), rank=1, updated_at=now - timedelta(seconds=10)
        )
        old = make_dispatch_row(
            DispatchStatus.PENDING,
            officer_id=uuid4(),
            rank=2,
            updated_at=now - timedelta(seconds=STALE_LOCATION_THRESHOLD_SECONDS + 60),
        )
        res = _build_alert_dispatch_res(ALERT_ID, [fresh, old])
 
        assert res.selected.is_location_stale is False
        assert res.pending[0].is_location_stale is True

class TestLoadAlertContext:
    @pytest.mark.asyncio
    async def test_row_maps_to_alert_context(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=make_first_result(
                (ALERT_ID, DetectionType.WEAPON_DETECTED, NEIGHBOURHOOD_ID, -26.2041, 28.0473)
            )
        )

        context = await _load_alert_context(mock_db, ALERT_ID)
        assert context == AlertContext(
            alert_id=ALERT_ID,
            detection_type="WEAPON_DETECTED",
            neighbourhood_id=NEIGHBOURHOOD_ID,
            latitude=-26.2041,
            longitude=28.0473,
        )

    @pytest.mark.asyncio
    async def test_returns_none_when_alert_does_not_exist(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=make_first_result(None))
        assert await _load_alert_context(mock_db, ALERT_ID) is None

    @pytest.mark.asyncio
    async def test_property_without_neighbourhood_or_coord_is_none(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=make_first_result(
                (ALERT_ID, DetectionType.WEAPON_DETECTED, None, None, None)
            )
        )

        context = await _load_alert_context(mock_db, ALERT_ID)
        assert context.neighbourhood_id is None
        assert context.latitude is None
        assert context.longitude is None

class TestFetchNeighbourhoodOfficers:
    @pytest.mark.asyncio
    async def test_query_is_scoped_to_neighbourhood_and_officer(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=make_rows_result([]))
        await _fetch_neighbourhood_officers(mock_db, NEIGHBOURHOOD_ID, -26.2041, 28.0473)

        stmt = mock_db.execute.await_args.args[0]
        params = compiled_params(stmt).values()
        sql = compiled_sql(stmt)

        assert NEIGHBOURHOOD_ID in params
        assert OTHER_NEIGHBOURHOOD_ID not in params
        assert NeighbourhoodRole.SECURITY_OFFICER in params
        assert "neighbourhood_user.neighbourhood" in sql
        assert "neighbourhood_user.role" in sql

    @pytest.mark.asyncio
    async def test_query_uses_alert_location(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=make_rows_result([]))
        await _fetch_neighbourhood_officers(mock_db, NEIGHBOURHOOD_ID, -26.2041, 28.0473)

        stmt = mock_db.execute.await_args.args[0]
        params = list(compiled_params(stmt).values())
        
        assert "ST_Distance" in compiled_sql(stmt)
        assert params.index(28.0473) < params.index(-26.2041)

    @pytest.mark.asyncio
    async def test_rows_mapped_to_candidates(self):
        a, b = uuid4(), uuid4()
        updated_at = datetime.now(timezone.utc)
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=make_rows_result([
            (a, AVAILABLE, updated_at, 812.5),
            (b, BUSY, None, None),
        ]))
        candidates = await _fetch_neighbourhood_officers(mock_db, NEIGHBOURHOOD_ID, -26.2041, 28.0473)

        assert candidates == [
            OfficerCandidate(a, AVAILABLE, updated_at, 812.5, 0),
            OfficerCandidate(b, BUSY, None, None, 0),
        ]

    @pytest.mark.asyncio
    async def test_no_officers_gives_empty_list(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=make_rows_result([]))
        assert await _fetch_neighbourhood_officers(mock_db, NEIGHBOURHOOD_ID, -26.2041, 28.0473) == []

class TestFetchWorkloads:
    @pytest.mark.asyncio
    async def test_no_officers_skips_the_query(self):
        mock_db = AsyncMock()
        assert await _fetch_workloads(mock_db, [], ALERT_ID) == {}
        mock_db.execute.assert_not_awaited()
 
    @pytest.mark.asyncio
    async def test_returns_counts_per_officer(self):
        a, b = uuid4(), uuid4()
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=make_rows_result([(a, 2), (b, 1)]))
 
        workloads = await _fetch_workloads(mock_db, [a, b, uuid4()], ALERT_ID)
        assert workloads == {a: 2, b: 1}
 
    @pytest.mark.asyncio
    async def test_only_counts_active_dispatches_on_unresolved_other_alerts(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=make_rows_result([]))
        await _fetch_workloads(mock_db, [uuid4()], ALERT_ID)
 
        params = list(compiled_params(mock_db.execute.await_args.args[0]).values())
 
        assert ALERT_ID in params  
        assert "RESOLVED" in params
        assert list(ACTIVE_DISPATCH_STATUS) in params

class TestDispatchAlert:
    @pytest.mark.asyncio
    async def test_raises_404_when_alert_missing(self):
        with pytest.raises(HTTPException) as exc_info:
            await run_dispatch([make_first_result(None)])

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Alert not found"

    @pytest.mark.asyncio
    async def test_non_critical_alerts_skipped(self):
        for detection_type in ("HUMAN_PRESENCE", "LOITERING", "PERIMETER_SCAN"):
            context = make_context(detection_type=detection_type)
            run = await run_dispatch([make_first_result(make_alert_row(context))])

            assert run.res.alert_id == ALERT_ID
            assert run.res.selected is None
            assert run.res.pending == []
            assert run.res.queued == []
            assert run.db.execute.await_count == 1
            run.db.add_all.assert_not_called()
            run.db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dispatces_critical_alerts(self):
        for detection_type in sorted(CRITICAL_DETECTION_TYPES):
            context = make_context(detection_type=detection_type)
            run = await run_dispatch(dispatch_steps(context, officers=[make_candidate()], workloads={}))

            assert run.res.selected is not None
            run.db.commit.assert_awaited_once()
            run.db.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_selects_nearest_available_and_queues_busy(self):
        near = make_candidate(distance=300.0)
        far = make_candidate(distance=900)
        busy = make_candidate(availability_status=BUSY, distance=50.0)
        run = await run_dispatch(
            dispatch_steps(
                make_context(), 
                officers=[far, busy, near], 
                workloads={}
            )
        )

        assert run.res.selected.officer_id == near.officer_id
        assert run.res.selected.status == DispatchStatus.SELECTED
        assert [c.officer_id for c in run.res.pending] == [far.officer_id]
        assert [c.officer_id for c in run.res.queued] == [busy.officer_id]
        assert run.res.no_candidate is False
        run.db.commit.assert_awaited_once()
        assert run.db.execute.await_count == 6

    @pytest.mark.asyncio
    async def test_busy_officer_is_never_given_an_active_alert_automatically(self):
        busy = make_candidate(availability_status=BUSY, distance=10.0)
        run = await run_dispatch(
            dispatch_steps(make_context(), officers=[busy], workloads={})
        )
 
        assert run.res.selected is None
        assert [c.officer_id for c in run.res.queued] == [busy.officer_id]
        assert run.res.no_candidate is True
        assert all(row.status != DispatchStatus.SELECTED for row in run.added)
        run.escalate.assert_awaited_once()
        assert run.escalate.await_args.kwargs["reason"] == "no_available_officer"

    @pytest.mark.asyncio
    async def test_ineligible_officers_are_never_dispatched(self):
        unavailable_officer = make_candidate(availability_status=UNAVAILABLE, distance=10.0)
        stale_officer = make_candidate(age=STALE_LOCATION_THRESHOLD_SECONDS + 60, distance=20.0)
        no_location = replace(make_candidate(distance=30.0), distance=None)
        eligible_officer = make_candidate(distance=4000.0)
 
        run = await run_dispatch(
            dispatch_steps(
                make_context(),
                officers=[unavailable_officer, stale_officer, no_location, eligible_officer],
                workloads={},
            )
        )
 
        dispatched = {row.officer_id for row in run.added if row.officer_id}
        assert dispatched == {eligible_officer.officer_id}
        assert run.res.selected.officer_id == eligible_officer.officer_id

    @pytest.mark.asyncio
    async def test_no_eligible_officers_records_no_candidate(self):
        officers = [
            make_candidate(availability_status=UNAVAILABLE),
            make_candidate(age=STALE_LOCATION_THRESHOLD_SECONDS + 60),
        ]
        run = await run_dispatch(dispatch_steps(make_context(), officers=officers))
 
        assert run.res.no_candidate is True
        assert run.res.selected is None
        assert [row.status for row in run.added] == [DispatchStatus.NO_CANDIDATE]
        run.db.commit.assert_awaited_once()
        run.escalate.assert_awaited_once()
        no_candidate_row, kwargs = run.escalate.await_args.args[1], run.escalate.await_args.kwargs
        assert no_candidate_row.status == DispatchStatus.NO_CANDIDATE
        assert kwargs["reason"] == "no_available_officer"

    @pytest.mark.asyncio
    async def test_no_officers_records_no_candidate(self):
        run = await run_dispatch(dispatch_steps(make_context(), officers=[]))
        assert run.res.no_candidate is True
        assert [row.status for row in run.added] == [DispatchStatus.NO_CANDIDATE]
        run.escalate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_only_officers_from_the_alerts_own_neighbourhood_are_queried(self):
        run = await run_dispatch(
            dispatch_steps(make_context(), officers=[make_candidate()], workloads={})
        )
        officer_query = run.db.execute.await_args_list[2].args[0]
        params = compiled_params(officer_query).values()
 
        assert NEIGHBOURHOOD_ID in params
        assert OTHER_NEIGHBOURHOOD_ID not in params
        assert NeighbourhoodRole.SECURITY_OFFICER in params

    @pytest.mark.asyncio
    async def test_only_eligible_officers_workload_is_recorded(self):
        eligible = make_candidate(distance=300.0)
        stale = make_candidate(age=STALE_LOCATION_THRESHOLD_SECONDS + 60)
        run = await run_dispatch(
            dispatch_steps(
                make_context(),
                officers=[eligible, stale],
                workloads={eligible.officer_id: 2},
            )
        )
 
        workload_query = run.db.execute.await_args_list[3].args[0]
        params = list(compiled_params(workload_query).values())
 
        assert [eligible.officer_id] in params
        assert ALERT_ID in params
        assert run.res.selected.workload == 2

    @pytest.mark.asyncio
    async def test_officers_without_dispatches_have_zero_workload(self):
        run = await run_dispatch(
            dispatch_steps(make_context(), officers=[make_candidate()], workloads={})
        )
        assert run.res.selected.workload == 0

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("fixed_weights")
    async def test_officer_with_lower_workload_selected(self):
        loaded = make_candidate(distance=500.0)
        idle = make_candidate(distance=500.0)
        run = await run_dispatch(
            dispatch_steps(
                make_context(),
                officers=[loaded, idle],
                workloads={loaded.officer_id: 3},
            )
        )
 
        assert run.res.selected.officer_id == idle.officer_id
        assert [c.officer_id for c in run.res.pending] == [loaded.officer_id]

def _handler_db(context, role=None, rows=()):
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        side_effect=[
            make_first_result(make_alert_row(context) if context is not None else None),
            make_scalar_result(role),
            make_scalars_result(rows),
        ]
    )
    return mock_db
class TestGetAlertDispatchHandler:
    @pytest.mark.asyncio
    async def test_membership_prevents_others_from_viewing_dispatch(self):
        mock_db = _handler_db(make_context(), role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN)
        await get_alert_dispatch_handler(alert_id=ALERT_ID, db=mock_db, claims=CLAIMS)

        membership_query = mock_db.execute.await_args_list[1].args[0]
        params = compiled_params(membership_query).values()

        assert NEIGHBOURHOOD_ID in params
        assert OTHER_NEIGHBOURHOOD_ID not in params
        assert CLAIMS["sub"] in params 

    @pytest.mark.asyncio
    async def test_allows_neighbourhood_admin(self):
        officer = uuid4()
        rows = [make_dispatch_row(DispatchStatus.SELECTED, officer_id=officer, rank=1)]
        mock_db = _handler_db(make_context(), role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN, rows=rows)
        res = await get_alert_dispatch_handler(alert_id=ALERT_ID, db=mock_db, claims=CLAIMS)

        assert res.alert_id == ALERT_ID
        assert res.selected.officer_id == officer
        assert mock_db.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_rejects_non_members(self):
        mock_db = _handler_db(make_context(), role=None)
        with pytest.raises(HTTPException) as exc_info:
            await get_alert_dispatch_handler(alert_id=ALERT_ID, db=mock_db, claims=CLAIMS)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Not authorised to view dispatch for this alert"
        assert mock_db.execute.await_count == 2            

    @pytest.mark.asyncio
    async def test_rejects_residents(self):
        mock_db = _handler_db(make_context(), role=NeighbourhoodRole.RESIDENT)
        with pytest.raises(HTTPException) as exc_info:
            await get_alert_dispatch_handler(alert_id=ALERT_ID, db=mock_db, claims=CLAIMS)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Not authorised to view dispatch for this alert"
        assert mock_db.execute.await_count == 2  

def _respond_db(*, officer, dispatch, extra=()):
    mock_db = AsyncMock()
    mock_db.add = Mock()
    mock_db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(officer),
            make_scalar_result(dispatch),
            *extra,
        ]
    )
    return mock_db
class TestRespondToDispatchHandler:
    @pytest.mark.asyncio
    async def test_accept_marks_dispatch_as_accepted(self): 
        officer_id = uuid4()
        officer = SimpleNamespace(id=officer_id)
        dispatch = make_dispatch_row(
            DispatchStatus.NOTIFIED,
            officer_id=officer_id,
            rank=1,
            notified_at=datetime.now(timezone.utc) - timedelta(seconds=5)
        )     
        mock_db = _respond_db(
            officer=officer,
            dispatch=dispatch,
            extra=[
                make_scalars_result([dispatch]),
                make_scalars_result([str(uuid4())]),
            ],
        )  

        with patch("app.services.dispatch_service.broadcast", new=AsyncMock()) as broadcast:
            res = await respond_to_dispatch_handler(dispatch.id, "ACCEPT", mock_db, CLAIMS)

        assert dispatch.status == DispatchStatus.ACCEPTED
        assert res.status == 200
        assert res.data.status == DispatchStatus.ACCEPTED
        mock_db.commit.assert_awaited_once()
        broadcast.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_decline_promotes_next(self):
        officer_id, next_officer_id = uuid4(), uuid4()
        officer = SimpleNamespace(id=officer_id)
        dispatch = make_dispatch_row(
            DispatchStatus.NOTIFIED,
            officer_id=officer_id,
            rank=1,
            notified_at=datetime.now(timezone.utc) - timedelta(seconds=5),
        )
        next_candidate = make_dispatch_row(DispatchStatus.PENDING, officer_id=next_officer_id, rank=2)
        mock_db = _respond_db(
            officer=officer,
            dispatch=dispatch,
            extra=[
                make_scalars_result([dispatch, next_candidate]),
                make_scalar_result(str(uuid4())),
                make_scalar_result("WEAPON_DETECTED"),
            ],
        )

        with patch("app.services.dispatch_service.broadcast", new=AsyncMock()) as broadcast:
            res = await respond_to_dispatch_handler(dispatch.id, "DECLINE", mock_db, CLAIMS)

        assert dispatch.status == DispatchStatus.DECLINED
        assert res.message == "Declined"
        assert next_candidate.status == DispatchStatus.NOTIFIED
        assert next_candidate.notified_at is not None
        broadcast.assert_awaited_once()
        assert broadcast.await_args.args[1]["payload"]["detection_type"] == "WEAPON_DETECTED"

    @pytest.mark.asyncio
    async def test_rejects_response_from_officer_it_was_not_sent_to(self):
        officer = SimpleNamespace(id=uuid4())
        dispatch = make_dispatch_row(DispatchStatus.NOTIFIED, officer_id=uuid4(), rank=1)
        mock_db = _respond_db(officer=officer, dispatch=dispatch)

        with pytest.raises(HTTPException) as exc_info:
            await respond_to_dispatch_handler(dispatch.id, "ACCEPT", mock_db, CLAIMS)

        assert exc_info.value.status_code == 403
        mock_db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_accept_fails_when_alert_assigned_to_another_officer(self):
        officer_id = uuid4()
        officer = SimpleNamespace(id=officer_id)
        dispatch = make_dispatch_row(
            DispatchStatus.NOTIFIED,
            officer_id=officer_id,
            rank=2,
            notified_at=datetime.now(timezone.utc) - timedelta(seconds=5),
        )
        already_accepted = make_dispatch_row(DispatchStatus.ACCEPTED, officer_id=uuid4(), rank=1)
        mock_db = _respond_db(
            officer=officer,
            dispatch=dispatch,
            extra=[make_scalars_result([already_accepted, dispatch])]
        )

        with pytest.raises(HTTPException) as exc_info:
            await respond_to_dispatch_handler(dispatch.id, "ACCEPT", mock_db, CLAIMS)

        assert exc_info.value.status_code == 409
        assert dispatch.status == DispatchStatus.NOTIFIED
        mock_db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_expired_request_cannot_be_accepted(self):
        officer_id = uuid4()
        officer = SimpleNamespace(id=officer_id)
        dispatch = make_dispatch_row(
            DispatchStatus.NOTIFIED,
            officer_id=officer_id,
            rank=1,
            notified_at=datetime.now(timezone.utc) - timedelta(seconds=RESPONSE_TIMEOUT + 30),
        )
        mock_db = _respond_db(
            officer=officer,
            dispatch=dispatch,
            extra=[make_scalars_result([dispatch])],
        )

        with patch("app.services.dispatch_service._escalate_dispatch", new=AsyncMock()) as escalate:
            with pytest.raises(HTTPException) as exc_info:
                await respond_to_dispatch_handler(dispatch.id, "ACCEPT", mock_db, CLAIMS)

        assert exc_info.value.status_code == 409
        assert dispatch.status == DispatchStatus.TIMED_OUT
        assert mock_db.commit.await_count == 2
        mock_db.add.assert_called_once()
        assert mock_db.add.call_args.args[0].status == DispatchStatus.NO_CANDIDATE
        escalate.assert_awaited_once()
        assert escalate.await_args.kwargs["reason"] == "no_available_officer"

class TestExpireStaleDispatches:
    @pytest.mark.asyncio
    async def test_expires_stale_dispatches(self):
        stale = make_dispatch_row(
            DispatchStatus.NOTIFIED,
            officer_id=uuid4(),
            rank=1,
            notified_at=datetime.now(timezone.utc) - timedelta(seconds=RESPONSE_TIMEOUT)
        )
        mock_db = AsyncMock()
        mock_db.add = Mock()
        mock_db.execute = AsyncMock(
            side_effect=[
                make_scalars_result([stale]),
                make_scalars_result([stale]),
            ]
        )

        with patch("app.services.dispatch_service._escalate_dispatch", new=AsyncMock()) as escalate:
            expired = await expire_stale_dispatchs(mock_db)

        assert expired == 1
        assert stale.status == DispatchStatus.TIMED_OUT
        mock_db.add.assert_called_once()
        escalate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rows_locked_and_skips_already_locked(self):
        mock_db = AsyncMock()
        mock_db.add = Mock()
        mock_db.execute = AsyncMock(return_value=make_scalars_result([]))

        await expire_stale_dispatchs(mock_db)

        stmt = mock_db.execute.await_args.args[0]
        sql = compiled_sql(stmt)
        assert "FOR UPDATE" in sql.upper()
        assert "SKIP LOCKED" in sql.upper()

class TestPromoteOfficer:
    async def promote(self, rows):
        mock_db, _ = make_mock_db()
        mock_db.execute = AsyncMock(return_value=make_scalars_result(rows))
        with (
            patch("app.services.dispatch_service._notify_officer", new=AsyncMock()) as notify, 
            patch("app.services.dispatch_service._escalate_dispatch", new=AsyncMock()) as escalate,
        ):
            await _promote_officer(mock_db, ALERT_ID)
        return SimpleNamespace(db=mock_db, notify=notify, escalate=escalate)

    @pytest.mark.asyncio
    async def test_already_accepted_stops_reassignment(self):
        accepted = make_dispatch_row(DispatchStatus.ACCEPTED, officer_id=uuid4(), rank=1)
        pending = make_dispatch_row(DispatchStatus.PENDING, officer_id=uuid4(), rank=2)
        run = await self.promote([accepted, pending])

        run.notify.assert_not_awaited()
        run.escalate.assert_not_awaited()
        run.db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_double_notify(self):
        notified = make_dispatch_row(DispatchStatus.NOTIFIED, officer_id=uuid4(), rank=1)
        pending = make_dispatch_row(DispatchStatus.PENDING, officer_id=uuid4(), rank=2)
        run = await self.promote([notified, pending])

        run.notify.assert_not_awaited()
        run.escalate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_promotes_next_officer_in_line(self):
        declined = make_dispatch_row(DispatchStatus.DECLINED, officer_id=uuid4(), rank=1)
        expired = make_dispatch_row(DispatchStatus.TIMED_OUT, officer_id=uuid4(), rank=2)
        pending = make_dispatch_row(DispatchStatus.PENDING, officer_id=uuid4(), rank=3)
        queued = make_dispatch_row(DispatchStatus.QUEUED, officer_id=uuid4(), rank=4)

        run = await self.promote([declined, expired, pending, queued])
        
        run.notify.assert_awaited_once_with(run.db, pending)
        run.escalate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_falls_back_to_queued_officer(self):
        declined = make_dispatch_row(DispatchStatus.DECLINED, officer_id=uuid4(), rank=1)
        queued = make_dispatch_row(DispatchStatus.QUEUED, officer_id=uuid4(), rank=2)
        run = await self.promote([declined, queued])
        run.notify.assert_awaited_once_with(run.db, queued)

    @pytest.mark.asyncio
    async def test_no_candidates_escalates(self):
        declined = make_dispatch_row(DispatchStatus.DECLINED, officer_id=uuid4(), rank=1)
        expired = make_dispatch_row(DispatchStatus.TIMED_OUT, officer_id=uuid4(), rank=2)
        run = await self.promote([declined, expired])

        run.notify.assert_not_awaited()
        run.db.add.assert_called_once()
        no_candidate = run.db.add.call_args.args[0]
        assert no_candidate.status == DispatchStatus.NO_CANDIDATE
        assert no_candidate.alert_id == ALERT_ID
        assert no_candidate.neighbourhood_id == NEIGHBOURHOOD_ID
        run.escalate.assert_awaited_once_with(run.db, no_candidate, reason="no_available_officer")

    @pytest.mark.asyncio
    async def test_no_duplicate_candidate_row_when_no_officers(self):
        declined = make_dispatch_row(DispatchStatus.DECLINED, officer_id=uuid4(), rank=1)
        no_candidate = make_dispatch_row(DispatchStatus.NO_CANDIDATE, officer_id=uuid4(), rank=None)

        run = await self.promote([declined, no_candidate])
        run.db.add.assert_not_called()
        run.escalate.assert_not_awaited()

class TestEscalateDispatch:
    def make_row(self, **overrides):
        return make_dispatch_row(DispatchStatus.NO_CANDIDATE, rank=None, **overrides)

    @pytest.mark.asyncio
    async def test_records_notified_at(self):
        mock_db, _ = make_mock_db()
        mock_db.execute = AsyncMock(return_value=make_scalars_result([str(uuid4())]))
        row = self.make_row()
        assert row.notified_at is None

        with patch("app.services.dispatch_service.broadcast", new=AsyncMock()):
            await _escalate_dispatch(mock_db, row, reason="no_available_officer")

        assert row.notified_at is not None
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(row)

    @pytest.mark.asyncio
    async def test_broadcasts_to_admins(self):
        admin_id = str(uuid4())
        mock_db, _ = make_mock_db()
        mock_db.execute = AsyncMock(return_value=make_scalars_result([admin_id]))
        row = self.make_row()

        with patch("app.services.dispatch_service.broadcast", new=AsyncMock()) as broadcast:
            await _escalate_dispatch(mock_db, row, reason="no_available_officer")

        params = compiled_params(mock_db.execute.await_args.args[0])
        roles_param = next(v for v in params.values() if isinstance(v, list))
        assert NeighbourhoodRole.NEIGHBOURHOOD_ADMIN in roles_param
        assert NeighbourhoodRole.SECURITY_OFFICER not in roles_param

        broadcast.assert_awaited_once()
        receivers, message = broadcast.await_args.args
        assert receivers == [admin_id]
        assert message["event"] == "dispatch.escalated"
        assert message["payload"]["dispatch_id"] == str(row.id)
        assert message["payload"]["alert_id"] == str(row.alert_id)
        assert message["payload"]["reason"] == "no_available_officer"

    @pytest.mark.asyncio
    async def test_no_admins_no_broadcast(self):
        mock_db, _ = make_mock_db()
        mock_db.execute = AsyncMock(return_value=make_scalars_result([]))
        row = self.make_row()

        with patch("app.services.dispatch_service.broadcast", new=AsyncMock()) as broadcast:
            await _escalate_dispatch(mock_db, row, reason="no_available_officer")

        broadcast.assert_not_awaited()
        assert row.notified_at is not None

class TestExpireStaleDispatch:
    @pytest.mark.asyncio
    async def test_skips_row_when_no_longer_notified_after_lock(self):
        stale = make_dispatch_row(
            DispatchStatus.NOTIFIED,
            officer_id=uuid4(),
            rank=1,
            notified_at=datetime.now(timezone.utc) - timedelta(seconds=RESPONSE_TIMEOUT + 30),
        )
        accepted = make_dispatch_row(
            DispatchStatus.ACCEPTED,
            officer_id=stale.officer_id,
            rank=1,
        )
        accepted.id = stale.id

        mock_db, _ = make_mock_db()
        mock_db.execute = AsyncMock(return_value=make_scalar_result(accepted))

        with patch("app.services.dispatch_service._promote_officer", new=AsyncMock()) as promote:
            result = await _expire_stale_dispatch(mock_db, stale)

        assert result is accepted
        assert result.status == DispatchStatus.ACCEPTED
        mock_db.commit.assert_not_awaited() 
        promote.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_expires_when_still_notified_after_lock(self):
        stale = make_dispatch_row(
            DispatchStatus.NOTIFIED,
            officer_id=uuid4(),
            rank=1,
            notified_at=datetime.now(timezone.utc) - timedelta(seconds=RESPONSE_TIMEOUT + 30)
        )

        mock_db, _ = make_mock_db()
        mock_db.execute = AsyncMock(return_value=make_scalar_result(stale))

        with patch("app.services.dispatch_service._promote_officer", new=AsyncMock()) as promote:
            result = await _expire_stale_dispatch(mock_db, stale)

        assert result.status == DispatchStatus.TIMED_OUT
        mock_db.commit.assert_awaited_once() 
        promote.assert_awaited_once_with(mock_db, stale.alert_id)

    @pytest.mark.asyncio
    async def test_within_window_nothing_happens(self):
        fresh = make_dispatch_row(
            DispatchStatus.NOTIFIED,
            officer_id=uuid4(),
            rank=1,
            notified_at=datetime.now(timezone.utc) - timedelta(seconds=5)
        )

        mock_db, _ = make_mock_db()
        mock_db.execute = AsyncMock(return_value=make_scalar_result(fresh))

        with patch("app.services.dispatch_service._promote_officer", new=AsyncMock()) as promote:
            result = await _expire_stale_dispatch(mock_db, fresh)

        assert result is fresh
        assert result.status == DispatchStatus.NOTIFIED
        mock_db.commit.assert_not_awaited() 
        promote.assert_not_awaited()