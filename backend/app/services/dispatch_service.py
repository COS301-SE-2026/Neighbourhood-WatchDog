import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func, cast
from sqlalchemy.exc import IntegrityError
from geoalchemy2 import Geography

from app.auth.authorization import Claims
from app.core.database import DbSession
from app.models.alert import Alert, AlertStatus
from app.models.camera import Camera
from app.models.user import User
from app.models.property import Property
from app.models.dispatch import Dispatch, DispatchStatus
from app.models.security_officer import SecurityOfficer, AvailabilityStatus
from app.models.neighbourhood_user import NeighbourhoodUser, NeighbourhoodRole
from app.schemas.dispatch import AlertDispatchRes, DispatchCandidateRes, RespondDispatchRes
from app.services.neighbourhood_service import STALE_LOCATION_THRESHOLD_SECONDS, is_location_stale
from app.api.controllers.alert import broadcast

logger = logging.getLogger(__name__)

CRITICAL_DETECTION_TYPES: frozenset[str] = frozenset({"WEAPON_DETECTED", "FALL_DETECTED"})
OFFICER_AVG_SPEED = 8.33 #m/s or about 30km/h
ROUTE_CIRCUITRY_FACTOR = 1.3 #road distance is about 30% longer than straight-line

RESPONSE_TIMEOUT = 120 #officer has 2min to accept a request before expiring

@dataclass(frozen=True)
class RankingWeights:
    """Score = eta_weight * ETA(min) + workload_weight * workload(no of active alerts) + freshness_weight * location_age_ratio"""
    eta_weight: float
    workload_weight: float
    freshness_weight: float

DEFAULT_WEIGHTS = RankingWeights(eta_weight=1.0, workload_weight=1.0, freshness_weight=0.5)

RANKING_WEIGHTS: dict[str, RankingWeights] = {
    "WEAPON_DETECTED": RankingWeights(eta_weight=1.5, workload_weight=0.25, freshness_weight=0.5),
    "FALL_DETECTED": RankingWeights(eta_weight=1.5, workload_weight=0.5, freshness_weight=0.5),
}

ACTIVE_DISPATCH_STATUS = (
    DispatchStatus.SELECTED,
    DispatchStatus.NOTIFIED,
    DispatchStatus.ACCEPTED,
)

#available officers rank ahead of busy officers
_AVAILABILITY_TIER: dict[AvailabilityStatus, int] = {
    AvailabilityStatus.AVAILABLE: 0,
    AvailabilityStatus.BUSY: 1,
}

#roles allowed to view dispatch details
DISPATCH_VIEWER_ROLES = (
    NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
    NeighbourhoodRole.SECURITY_OFFICER,
)

#officers who haven't been notified
_UNCONTACTED_DISPATCH_STATUS = (
    DispatchStatus.SELECTED,
    DispatchStatus.PENDING,
    DispatchStatus.QUEUED,
)

@dataclass(frozen=True)
class AlertContext:
    alert_id: UUID
    detection_type: str
    neighbourhood_id: UUID | None
    latitude: float | None
    longitude: float | None

@dataclass(frozen=True)
class OfficerCandidate:
    officer_id: UUID
    availability_status: AvailabilityStatus | None
    location_updated_at: datetime | None
    distance: float | None
    workload: int = 0

@dataclass(frozen=True)
class RankedCandidate:
    candidate: OfficerCandidate
    eta: float
    score: float
    rank: int

def _enum_value(value) -> str:
    return str(getattr(value, "value", value))

def filter_eligible(candidates: list[OfficerCandidate]) -> list[OfficerCandidate]:
    """Returns eligible officers who can be dispatched"""
    """Unavailable officers, officers without a location and officers with stale location are excluded"""
    eligible: list[OfficerCandidate] = []
    for c in candidates:
        if c.availability_status not in _AVAILABILITY_TIER:
            continue
        if c.distance is None or c.location_updated_at is None:
            continue
        if is_location_stale(c.location_updated_at):
            continue
        eligible.append(c)
    return eligible

def estimate_eta_seconds(distance: float) -> float:
    """Estimate of ETA from straight line distance - Needs to be replaced with something more accurate"""
    return distance * ROUTE_CIRCUITRY_FACTOR / OFFICER_AVG_SPEED

def rank_candidates(
        eligible: list[OfficerCandidate],
        detection_type: str,
        now: datetime | None = None,
) -> list[RankedCandidate]:
    """Ranks eligible officers by availability and weighted scores, distance and officer_id used for tie-breaking"""
    now = now or datetime.now(timezone.utc)
    weights = RANKING_WEIGHTS.get(detection_type, DEFAULT_WEIGHTS)

    scored: list[tuple[OfficerCandidate, float, float, int]] = []
    for e in eligible:
        assert e.distance is not None
        assert e.location_updated_at is not None
        assert e.availability_status is not None
        eta = estimate_eta_seconds(e.distance)
        age = max((now - e.location_updated_at).total_seconds(), 0.0)
        freshness_ratio = min(age/STALE_LOCATION_THRESHOLD_SECONDS, 1.0)
        score = (
            weights.eta_weight * (eta/60.0)
            + weights.workload_weight * e.workload
            + weights.freshness_weight * freshness_ratio
        )
        scored.append((e, eta, score, _AVAILABILITY_TIER[e.availability_status]))

    scored.sort(
        key=lambda t: (
            t[3],
            t[2],
            t[0].distance,
            str(t[0].officer_id),
        )
    )
    return [
        RankedCandidate(candidate=e, eta=eta, score=score, rank=rank)
        for rank, (e, eta, score, _) in enumerate(scored, start=1)
    ]

def _build_dispatch_rows(context: AlertContext, ranked: list[RankedCandidate]) -> list[Dispatch]:
    """Helper to build dispatch table rows"""
    rows: list[Dispatch] = []
    has_selected = False

    for r in ranked:
        c = r.candidate
        if not has_selected:
            status = DispatchStatus.SELECTED
            has_selected = True
        elif c.availability_status == AvailabilityStatus.AVAILABLE:
            status = DispatchStatus.PENDING
        else:
            status = DispatchStatus.QUEUED

        rows.append(
            Dispatch(
                alert_id=context.alert_id,
                neighbourhood_id=context.neighbourhood_id,
                officer_id=c.officer_id,
                rank=r.rank,
                score=r.score,
                distance=c.distance,
                eta=r.eta,
                workload=c.workload,
                officer_availability=c.availability_status,
                officer_location_updated_at=c.location_updated_at,
                status=status,
            )
        )

    if not has_selected:
        rows.append(
            Dispatch(
                alert_id=context.alert_id,
                neighbourhood_id=context.neighbourhood_id,
                status=DispatchStatus.NO_CANDIDATE,
            )
        )
    return rows

async def _load_alert_context(db: DbSession, alert_id: UUID) -> AlertContext | None:
    stmt = (
        select(Alert.id, Alert.detection_type, Property.neighbourhood_id, Property.latitude, Property.longitude)
        .join(Camera, Camera.id == Alert.camera_id)
        .join(Property, Property.id == Camera.property_id)
        .where(Alert.id == alert_id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    
    return AlertContext(
        alert_id=row[0],
        detection_type=_enum_value(row[1]),
        neighbourhood_id=row[2],
        latitude=row[3],
        longitude=row[4],
    )

async def _fetch_neighbourhood_officers(
        db: DbSession,
        neighbourhood_id: UUID,
        latitude: float,
        longitude: float,
) -> list[OfficerCandidate]:
    alert_point = cast(
        func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
        Geography(geometry_type="POINT", srid=4326),
    )
    distance_expr = func.ST_Distance(SecurityOfficer.last_known_location, alert_point)

    stmt = (
        select(
            SecurityOfficer.id,
            SecurityOfficer.availability_status,
            SecurityOfficer.location_updated_at,
            distance_expr,
        ).join(NeighbourhoodUser, NeighbourhoodUser.id == SecurityOfficer.neighbourhood_user_id)
        .where(NeighbourhoodUser.neighbourhood_id == neighbourhood_id)
        .where(NeighbourhoodUser.role == NeighbourhoodRole.SECURITY_OFFICER)
    )
    result = await db.execute(stmt)

    return [
        OfficerCandidate(
            officer_id=officer_id,
            availability_status=availability,
            location_updated_at=updated_at,
            distance=float(distance) if distance is not None else None,
        )
        for officer_id, availability, updated_at, distance in result.all()
    ]

async def _fetch_workloads(
        db: DbSession,
        officer_ids: list[UUID],
        exclude_alert_id: UUID,
) -> dict[UUID, int]:
    """Number of unresolved alerts each officer has"""
    if not officer_ids:
        return {}
    stmt = (
        select(Dispatch.officer_id, func.count(Dispatch.id))
        .select_from(Dispatch)
        .join(Alert, Alert.id == Dispatch.alert_id)
        .where(Dispatch.officer_id.in_(officer_ids))
        .where(Dispatch.status.in_(ACTIVE_DISPATCH_STATUS))
        .where(Dispatch.alert_id != exclude_alert_id)
        .where(Alert.status != AlertStatus.RESOLVED.value)
        .group_by(Dispatch.officer_id)
    )
    result = await db.execute(stmt)
    return {officer_id: count for officer_id, count in result.all()}

async def _fetch_dispatch_rows(db: DbSession, alert_id: UUID) -> list[Dispatch]:
    stmt = (
        select(Dispatch)
        .where(Dispatch.alert_id == alert_id)
        .order_by(Dispatch.rank.asc().nulls_last(), Dispatch.created_at.asc())
    )
    return list((await db.execute(stmt)).scalars().all())

async def _get_officer_user_id(db: DbSession, officer_id: UUID) -> str | None:
    result = await db.execute(
        select(NeighbourhoodUser.user_id)
        .join(SecurityOfficer, SecurityOfficer.neighbourhood_user_id == NeighbourhoodUser.id)
        .where(SecurityOfficer.id == officer_id)
    )
    user_id = result.scalar_one_or_none()
    return str(user_id) if user_id is not None else None

async def get_dispatch_viewer_ids(
        db: DbSession, 
        neighbourhood_id: UUID | None,
        roles: tuple[NeighbourhoodRole, ...] = DISPATCH_VIEWER_ROLES,
        ) -> list[str]:
    if neighbourhood_id is None:
        return []
    
    result = await db.execute(
        select(NeighbourhoodUser.user_id)
        .where(NeighbourhoodUser.neighbourhood_id == neighbourhood_id)
        .where(NeighbourhoodUser.role.in_(roles))
    )
    return [str(user_id) for user_id in result.scalars().all()]

async def resolve_officer(db: DbSession, claims: Claims) -> SecurityOfficer:
    result = await db.execute(
        select(SecurityOfficer)
        .join(NeighbourhoodUser, NeighbourhoodUser.id == SecurityOfficer.neighbourhood_user_id)
        .join(User, User.id == NeighbourhoodUser.user_id)
        .where(User.cognito_sub == claims["sub"])
    )
    officer = result.scalar_one_or_none()

    if officer is None:
        raise HTTPException(403, "Not authorised: no security officer profile for this account")
    return officer

async def _notify_officer(db: DbSession, dispatch: Dispatch) -> None:
    """Notifies selected officer of dispatch request over websocket"""
    now = datetime.now(timezone.utc)
    dispatch.status = DispatchStatus.NOTIFIED
    dispatch.notified_at = now
    await db.commit()
    await db.refresh(dispatch)

    try:
        user_id = await _get_officer_user_id(db, dispatch.officer_id)
        if user_id is None:
            logger.warning(
                "dispatch: could not resolve user for officer %s (dispatch %s)",
                dispatch.officer_id, dispatch.id,
            )
            return

        await broadcast(
            [user_id],
            {
                "event": "dispatch.notified",
                "payload": {
                    "dispatch_id": str(dispatch.id),
                    "alert_id": str(dispatch.alert_id),
                    "distance": dispatch.distance,
                    "eta": dispatch.eta,
                    "notified_at": now.isoformat(),
                    "expires_at": (now + timedelta(seconds=RESPONSE_TIMEOUT)).isoformat(),
                },
            },
        )
    except Exception:
        logger.exception(
            "dispatch: failed to notify officer %s for dispatch %s",
            dispatch.officer_id, dispatch.id,
        )

async def _promote_officer(db: DbSession, alert_id: UUID) -> None:
    """
    Notifies next ranked officer if the selected officer declines, is unreachable, 
    or the request times out before a response is received. Picks officers from pending before
    picking from queued
    """
    result = await db.execute(
        select(Dispatch)
        .where(Dispatch.alert_id == alert_id)
        .order_by(Dispatch.rank.asc().nulls_last())
        .with_for_update()
    )
    rows = list(result.scalars().all())

    if not rows:
        return

    if any(r.status == DispatchStatus.ACCEPTED for r in rows):
        return

    if any(r.status == DispatchStatus.NOTIFIED for r in rows):
        return

    officer = next((r for r in rows if r.status in _UNCONTACTED_DISPATCH_STATUS), None)

    if officer is None:
        if not any(r.status == DispatchStatus.NO_CANDIDATE for r in rows):
            no_candidate = Dispatch(
                alert_id=alert_id,
                neighbourhood_id=rows[0].neighbourhood_id,
                status=DispatchStatus.NO_CANDIDATE,
            )
            db.add(no_candidate)
            await db.commit()
            await db.refresh(no_candidate)
            logger.info(
                "dispatch: no remaining candidates to notify for alert %s, escalating to neighbourhood_admin", 
                alert_id,
            )
            await _escalate_dispatch(db, no_candidate, reason="no_candidates")
        return

    await _notify_officer(db, officer)

async def _expire_stale_dispatch(db: DbSession, dispatch: Dispatch) -> Dispatch:
    """
    Sets a notified dispatch attempt to timed out 
    if the officer does not accept/decline within the response window
    """
    if dispatch.status != DispatchStatus.NOTIFIED or dispatch.notified_at is None:
        return dispatch

    locked_result = await db.execute(
        select(Dispatch).where(Dispatch.id == dispatch.id).with_for_update()
    )
    dispatch = locked_result.scalar_one()

    if dispatch.status != DispatchStatus.NOTIFIED or dispatch.notified_at is None:
        return dispatch

    now = datetime.now(timezone.utc)
    if (now - dispatch.notified_at).total_seconds() <= RESPONSE_TIMEOUT:
        return dispatch

    dispatch.status = DispatchStatus.TIMED_OUT
    dispatch.responded_at = now
    await db.commit()
    await db.refresh(dispatch)

    try:
        await _promote_officer(db, dispatch.alert_id)
    except Exception:
        logger.exception("dispatch: failed to promote next officer after time out for alert %s", dispatch.alert_id)

    return dispatch

async def expire_stale_dispatchs(db: DbSession) -> int:
    """Used to run through every dispatch attempt and sets to timed out"""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=RESPONSE_TIMEOUT)

    result = await db.execute(
        select(Dispatch).where(
            Dispatch.status == DispatchStatus.NOTIFIED,
            Dispatch.notified_at < cutoff,
        ).with_for_update(skip_locked=True)
    )

    expired = list(result.scalars().all())
    if not expired:
        return 0

    alert_ids: set[UUID] = set()
    for e in expired:
        e.status = DispatchStatus.TIMED_OUT
        e.responded_at = now
        alert_ids.add(e.alert_id)
    await db.commit()

    for alert_id in alert_ids:
        try:
            await _promote_officer(db, alert_id)
        except Exception:
            logger.exception("expire_stale_dispatches: failed to promote next officer for alert %s", alert_id)

    return len(expired)

async def _escalate_dispatch(db: DbSession, dispatch: Dispatch, reason: str) -> None:
    """Informs admin of critical alert no officer was able to attend to"""
    now = datetime.now(timezone.utc)
    dispatch.notified_at = now
    await db.commit()
    await db.refresh(dispatch)

    try:
        admin_ids = await get_dispatch_viewer_ids(
            db, dispatch.neighbourhood_id, roles=(NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,)
        )
        if not admin_ids:
            logger.warning(
                "dispatch: no neighbourhood admin to notify about alert %s", 
                dispatch.alert_id,
            )
            return
        
        await broadcast(
            admin_ids,
            {
                "event": "dispatch.escalated",
                "payload": {
                    "dispatch_id": str(dispatch.id),
                    "alert_id": str(dispatch.alert_id),
                    "neighbourhood_id": str(dispatch.neighbourhood_id) if dispatch.neighbourhood_id else None,
                    "reason": reason,
                    "notified_at": now.isoformat(),
                },
            },
        )
    except Exception:
        logger.exception(
            "dispatch: failed to broadcast escalation for alert %s",
            dispatch.alert_id,
        )

def _build_candidate_res(d: Dispatch) -> DispatchCandidateRes:
    return DispatchCandidateRes(
        id=d.id,
        alert_id=d.alert_id,
        officer_id=d.officer_id,
        rank=d.rank,
        score=d.score,
        distance=d.distance,
        eta=d.eta,
        workload=d.workload,
        status=d.status,
        officer_availability=d.officer_availability,
        is_location_stale=is_location_stale(d.officer_location_updated_at),
        created_at=d.created_at,
        notified_at=d.notified_at,
        responded_at=d.responded_at,
    )

def _build_alert_dispatch_res(alert_id: UUID, rows: list[Dispatch]) -> AlertDispatchRes:
    selected: DispatchCandidateRes| None = None
    pending: list[DispatchCandidateRes] = []
    queued: list[DispatchCandidateRes] = []
    no_candidate = False

    for d in rows:
        if d.status in ACTIVE_DISPATCH_STATUS:
            if selected is None:
                selected = _build_candidate_res(d)
        elif d.status == DispatchStatus.PENDING:
            pending.append(_build_candidate_res(d))
        elif d.status == DispatchStatus.QUEUED:
            queued.append(_build_candidate_res(d))
        elif d.status == DispatchStatus.NO_CANDIDATE:
            no_candidate = True

    return AlertDispatchRes(
        alert_id=alert_id,
        selected=selected,
        pending=pending,
        queued=queued,
        no_candidate=no_candidate,
    )

async def dispatch_alert(db: DbSession, alert_id: UUID) -> AlertDispatchRes:
    """Ranks officers for an alert and records dispatch attempts"""
    context = await _load_alert_context(db, alert_id)
    if context is None:
        raise HTTPException(404, "Alert not found")

    if context.detection_type not in CRITICAL_DETECTION_TYPES:
        logger.info("dispatch_alert skipped: alert %s (%s) is not critical", alert_id, context.detection_type)
        return AlertDispatchRes(alert_id=alert_id)

    existing = await _fetch_dispatch_rows(db, alert_id)
    if existing:
        return _build_alert_dispatch_res(alert_id, existing)

    try:
        ranked: list[RankedCandidate] = []

        if context.neighbourhood_id is None:
            logger.warning("dispatch_alert: alert %s belongs to a property with no neighbourhood", alert_id)
        elif context.latitude is None or context.longitude is None:
            logger.warning("dispatch_alert: alert %s property has no coordinates", alert_id)
        else:
            officers = await _fetch_neighbourhood_officers(
                db, context.neighbourhood_id, context.latitude, context.longitude
            )
            eligible = filter_eligible(officers)
            logger.info(
                "dispatch_alert: alert %s - %d officers in neighbourhood, %d eligible",
                alert_id, len(officers), len(eligible),
            )

            workloads = await _fetch_workloads(db, [e.officer_id for e in eligible], alert_id)
            eligible = [replace(e, workload=workloads.get(e.officer_id, 0)) for e in eligible]
            ranked = rank_candidates(eligible, context.detection_type)

            db.add_all(_build_dispatch_rows(context, ranked))
            await db.commit()

            selected_result = await db.execute(
                select(Dispatch).where(
                    Dispatch.alert_id == alert_id,
                    Dispatch.status == DispatchStatus.SELECTED,
                )
            )
            selected = selected_result.scalar_one_or_none()

            if selected is not None:
                await _notify_officer(db, selected)
    except IntegrityError:
        await db.rollback()
        existing = await _fetch_dispatch_rows(db, alert_id)
        if existing:
            return _build_alert_dispatch_res(alert_id, existing)
        logger.exception("dispatch_alert failed for alert %s", alert_id)
        raise HTTPException(500, "Failed to dispatch alert")
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        logger.exception("dispatch_alert failed for alert %s", alert_id)
        raise HTTPException(500, "Failed to dispatch alert")

    rows = await _fetch_dispatch_rows(db, alert_id)
    return _build_alert_dispatch_res(alert_id, rows)

async def get_alert_dispatch_handler(
        alert_id: UUID,
        db: DbSession,
        claims: Claims,
) -> AlertDispatchRes:
    """Returns selected, queued and pending officers for an alert"""
    if not claims:
        raise HTTPException(401, "Not authenticated")

    context = await _load_alert_context(db, alert_id)
    if context is None:
        raise HTTPException(404, "Alert not found")
    if context.neighbourhood_id is None:
        raise HTTPException(403, "Not authorised to view dispatch for this alert")

    role_result = await db.execute(
        select(NeighbourhoodUser.role)
        .join(User, User.id == NeighbourhoodUser.user_id)
        .where(User.cognito_sub == claims["sub"])
        .where(NeighbourhoodUser.neighbourhood_id == context.neighbourhood_id)
    )
    role = role_result.scalars().first()
    if role not in DISPATCH_VIEWER_ROLES:
        raise HTTPException(403, "Not authorised to view dispatch for this alert")

    rows = await _fetch_dispatch_rows(db, alert_id)

    notified = next((d for d in rows if d.status == DispatchStatus.NOTIFIED), None)
    if notified is not None:
        expired = await _expire_stale_dispatch(db, notified)
        if expired.status != DispatchStatus.NOTIFIED:
            rows = await _fetch_dispatch_rows(db, alert_id)

    return _build_alert_dispatch_res(alert_id, rows)

async def respond_to_dispatch_handler(
        dispatch_id: UUID,
        action: str,
        db: DbSession,
        claims: Claims,
) -> RespondDispatchRes:
    """Handles officer response to dispatch requests"""
    if not claims:
        raise HTTPException(401, "Not authenticated")

    officer = await resolve_officer(db, claims)

    result = await db.execute(
        select(Dispatch).where(Dispatch.id == dispatch_id).with_for_update()
    )
    dispatch = result.scalar_one_or_none()
    if dispatch is None:
        raise HTTPException(404, "Dispatch request not found")

    if dispatch.officer_id != officer.id:
        raise HTTPException(403, "This dispatch request was not sent to you")

    if dispatch.status == DispatchStatus.ACCEPTED:
        raise HTTPException(409, "This dispatch request has already been assigned")
    
    if dispatch.status in (DispatchStatus.DECLINED, DispatchStatus.TIMED_OUT):
        raise HTTPException(409, "This dispatch request is no longer available")
    
    if dispatch.status != DispatchStatus.NOTIFIED:
        raise HTTPException(409, "This dispatch request has not been offered to you yet")

    now = datetime.now(timezone.utc)
    if dispatch.notified_at is not None and (now - dispatch.notified_at).total_seconds() > RESPONSE_TIMEOUT:
        dispatch.status = DispatchStatus.TIMED_OUT
        dispatch.responded_at = now
        await db.commit()
        try:
            await _promote_officer(db, dispatch.alert_id)
        except Exception:
            logger.exception(
                "respond_to_dispatch: failed to promote next officer after expiry for alert %s", 
                dispatch.alert_id,
            )
        raise HTTPException(409, "This dispatch request has expired")

    if action == "DECLINE":
        dispatch.status = DispatchStatus.DECLINED
        dispatch.responded_at = now
        await db.commit()
        await db.refresh(dispatch)

        try:
            await _promote_officer(db, dispatch.alert_id)
        except Exception:
            logger.exception(
                "respond_to_dispatch: failed to promote next officer after declining alert %s",
                dispatch.alert_id,
            )

        return RespondDispatchRes(status=200, message="Declined", data=_build_candidate_res(dispatch))

    if action == "ACCEPT":
        lock_result = await db.execute(
            select(Dispatch)
            .where(Dispatch.alert_id == dispatch.alert_id)
            .with_for_update()
        )
        alert_rows = lock_result.scalars().all()

        if any(r.status == DispatchStatus.ACCEPTED and r.id != dispatch.id for r in alert_rows):
            raise HTTPException(409, "This alert has already been assigned to another officer")

        dispatch.status = DispatchStatus.ACCEPTED
        dispatch.responded_at = now

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(409, "This alert has already been assigned to another officer")

        await db.refresh(dispatch)

        try:
            user_ids = await get_dispatch_viewer_ids(db, dispatch.neighbourhood_id)
            if user_ids:
                await broadcast(
                    user_ids,
                    {
                        "event": "dispatch.accepted",
                        "payload": {
                            "dispatch_id": str(dispatch.id),
                            "alert_id": str(dispatch.alert_id),
                        },
                    },
                )
        except Exception:
            logger.exception(
                "respond_to_dispatch: failed to broadcast acceptance for dispatch %s",
                dispatch.id,
            )

        return RespondDispatchRes(status=200, message="Accepted", data=_build_candidate_res(dispatch))

    raise HTTPException(400, "Unsupported action")