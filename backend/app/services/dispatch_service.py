import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTPPException
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
from app.schemas.dispatch import AlertDispatchRes, DispatchCandidateRes
from app.services.security_officer_service import STALE_LOCATION_THRESHOLD_SECONDS, is_location_stale

logger = logging.getLogger(__name__)

CRITICAL_DETECTION_TYPES: frozenset[str] = frozenset({"WEAPON_DETECTED", "FALL_DETECTED"})
OFFICER_AVG_SPEED = 8.33 #m/s or about 30km/h
ROUTE_CIRCUITRY_FACTOR = 1.3 #road distance is about 30% longer than straight-line

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

@dataclass(frozen=True)
class AlertContext:
    alert_id: UUID
    detction_type: str
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

    scored: list[tuple[OfficerCandidate, float, float]] = []
    for e in eligible:
        eta = estimate_eta_seconds(e.distance)
        age = max((now - e.location_updated_at).total_seconds(), 0.0)
        freshness_ratio = min(age/STALE_LOCATION_THRESHOLD_SECONDS, 1.0)
        score = (
            weights.eta_weight * (eta/60.0)
            + weights.workload_weight * e.workload
            + weights.freshness_weight * freshness_ratio
        )
        scored.append((e, eta, score))

    scored.sort(
        key=lambda t: (
            _AVAILABILITY_TIER[t[0].availability_status],
            t[2],
            t[0].distance,
            str(t[0].officer_id),
        )
    )
    return [
        RankedCandidate(candidate=e, eta=eta, score=score, rank=rank)
        for rank, (e, eta, score) in enumerate(scored, start=1)
    ]

def _build_dispatch_rows(context: AlertContext, ranked: list[RankedCandidate]) -> list[Dispatch]:
    """Helper to build dispatch table rows"""
    rows: list[Dispatch] = []
    has_selected = False

    for r in ranked:
        c = r.candidate
        if c.availability_status == AvailabilityStatus.AVAILABLE:
            status = DispatchStatus.PENDING if has_selected else DispatchStatus.SELECTED
            has_selected = True
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
                officer_availability=c.availability,
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
        raise HTPPException(404, "Alert not found")

    if context.detction_type not in CRITICAL_DETECTION_TYPES:
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
            ranked = rank_candidates(eligible, context.detction_type)

            db.add_all(_build_dispatch_rows(context, ranked))
            await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await _fetch_dispatch_rows(db, alert_id)
        if existing:
            return _build_alert_dispatch_res(alert_id, existing)
        logger.exception("dispatch_alert failed for alert %s", alert_id)
        raise HTPPException(500, "Failed to dispatch alert")
    except HTPPException:
        raise
    except Exception:
        await db.rollback()
        logger.exception("dispatch_alert failed for alert %s", alert_id)
        raise HTPPException(500, "Failed to dispatch alert")

    rows = await _fetch_dispatch_rows(db, alert_id)
    return _build_alert_dispatch_res(alert_id, rows)