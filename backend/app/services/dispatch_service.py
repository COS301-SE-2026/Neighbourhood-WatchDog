from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTPPException
from sqlalchemy import select, func, cast
from geoalchemy2 import Geography

from app.auth.authorization import Claims
from app.core.database import DbSession
from app.models.alert import Alert, DetectionType
from app.models.camera import Camera
from app.models.user import User
from app.models.property import Property
from app.models.dispatch import Dispatch, DispatchStatus
from app.models.security_officer import SecurityOfficer, AvailabilityStatus
from app.models.neighbourhood_user import NeighbourhoodUser, NeighbourhoodRole
from app.schemas.dispatch import AlertDispatchRes, DispatchCandidateRes
from app.services.security_officer_service import STALE_LOCATION_THRESHOLD_SECONDS, is_location_stale

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