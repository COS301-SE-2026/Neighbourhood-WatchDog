from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.auth.authorization import NeighbourhoodMemberClaims
from app.models.alert import Alert, AlertStatus, DetectionType
from app.models.camera import Camera
from app.models.incident import Incident
from app.models.neighbourhood_user import (
    NeighbourhoodRole,
    NeighbourhoodUser,
)
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.schemas.alert import (
    AlertRes,
    IncidentDetailRes,
    IncidentSummaryRes,
)

def _build_incident_alert_response(alert: Alert) -> AlertRes:
    from app.services.alert_service import _build_alert_res

    return _build_alert_res(alert)

async def create_incident_for_alert(
    *,
    db: AsyncSession,
    alert: Alert,
) -> Incident:
    """Create a new Incident and attach the supplied Alert to it."""

    incident = Incident(
        detection_type=(
            alert.detection_type.value
            if hasattr(alert.detection_type, "value")
            else str(alert.detection_type)
        ),
        started_at=alert.frame_timestamp,
        last_seen_at=alert.frame_timestamp,
    )

    db.add(incident)
    await db.flush()

    alert.incident_id = incident.id
    alert.incident = incident

    return incident


async def ensure_incident_for_alert(
    *,
    db: AsyncSession,
    alert: Alert,
) -> Incident:
    """
    Attach a legacy alert to an Incident if it does not have one.
    Existing grouped alerts are updated lazily.
    """

    incident_id = getattr(alert, "incident_id", None)

    if incident_id is None:
        return await create_incident_for_alert(
            db=db,
            alert=alert,
        )

    incident = await db.get(Incident, incident_id)

    if incident is None:
        return await create_incident_for_alert(
            db=db,
            alert=alert,
        )

    if alert.frame_timestamp > incident.last_seen_at:
        incident.last_seen_at = alert.frame_timestamp

    return incident


def _incident_alerts(incident: Incident) -> list[Alert]:
    return sorted(
        list(incident.alerts or []),
        key=lambda alert: (
            alert.frame_timestamp,
            alert.created_at,
            alert.id,
        ),
    )


def _summary_for_incident(incident: Incident) -> IncidentSummaryRes:
    alerts = _incident_alerts(incident)

    if not alerts:
        raise HTTPException(
            status_code=500,
            detail="Incident has no alerts",
        )

    representative = alerts[-1]

    return IncidentSummaryRes(
        id=incident.id,
        detection_type=incident.detection_type,
        started_at=incident.started_at,
        last_seen_at=incident.last_seen_at,
        alert_count=len(alerts),
        representative_alert_id=representative.id,
        representative_alert=_build_incident_alert_response(representative)
    )


def _detail_for_incident(incident: Incident) -> IncidentDetailRes:
    alerts = _incident_alerts(incident)

    return IncidentDetailRes(
        id=incident.id,
        detection_type=incident.detection_type,
        started_at=incident.started_at,
        last_seen_at=incident.last_seen_at,
        alert_count=len(alerts),
        alerts=[
            _build_incident_alert_response(alert)
            for alert in alerts
        ],
    )


def _incident_query(
    neighbourhood_id: UUID,
):
    return (
        select(Incident)
        .join(Alert, Alert.incident_id == Incident.id)
        .join(Camera, Alert.camera_id == Camera.id)
        .join(Property, Camera.property_id == Property.id)
        .options(
            joinedload(Incident.alerts)
            .joinedload(Alert.camera)
            .joinedload(Camera.property),
            joinedload(Incident.alerts)
            .joinedload(Alert.tracking_subject),
        )
        .where(
            Property.neighbourhood_id == neighbourhood_id,
        )
        .distinct()
    )


async def list_incidents_handler(
    *,
    neighbourhood_id: UUID,
    db: AsyncSession,
    claims: dict,
    status_filter: str | None = None,
    camera_id: UUID | None = None,
    detection_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 25,
    offset: int = 0,
) -> tuple[list[IncidentSummaryRes], int]:

    from app.services.alert_service import _require_neighbourhood_membership

    membership = await _require_neighbourhood_membership(
        db,
        claims,
        neighbourhood_id,
    )

    current_user_id = UUID(str(claims["id"]))

    stmt = _incident_query(neighbourhood_id)

    if membership.role == NeighbourhoodRole.SECURITY_OFFICER:
        stmt = stmt.where(
            Incident.detection_type.in_(
                {
                    DetectionType.WEAPON_DETECTED.value,
                    DetectionType.FALL_DETECTED.value,
                }
            )
        )

    elif membership.role == NeighbourhoodRole.RESIDENT:
        stmt = stmt.join(
            PropertyUser,
            PropertyUser.property_id == Property.id,
        ).where(
            PropertyUser.user_id == current_user_id,
        )

    if status_filter:
        stmt = stmt.where(
            Alert.status == status_filter,
        )

    if camera_id:
        stmt = stmt.where(
            Alert.camera_id == camera_id,
        )

    if detection_type:
        stmt = stmt.where(
            Incident.detection_type == detection_type,
        )

    if start_date:
        stmt = stmt.where(
            Incident.last_seen_at >= start_date,
        )

    if end_date:
        stmt = stmt.where(
            Incident.started_at <= end_date,
        )

    count_stmt = select(func.count()).select_from(
        stmt.with_only_columns(Incident.id)
        .order_by(None)
        .distinct()
        .subquery()
    )

    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    result = await db.execute(
        stmt
        .order_by(
            Incident.last_seen_at.desc(),
            Incident.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    incidents = result.unique().scalars().all()

    return [
        _summary_for_incident(incident)
        for incident in incidents
    ], total


async def get_incident_handler(
    *,
    incident_id: UUID,
    db: AsyncSession,
    claims: dict,
) -> IncidentDetailRes:

    from app.services.alert_service import _require_neighbourhood_membership

    stmt = _incident_query(
        neighbourhood_id=(
            select(Property.neighbourhood_id)
            .join(Camera, Camera.property_id == Property.id)
            .join(Alert, Alert.camera_id == Camera.id)
            .where(Alert.incident_id == incident_id)
            .limit(1)
            .scalar_subquery()
        )
    ).where(Incident.id == incident_id)

    result = await db.execute(stmt)
    incident = result.unique().scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    # Recheck membership against the incident's neighbourhood.
    first_alert = _incident_alerts(incident)[0]

    property_result = await db.execute(
        select(Property)
        .join(Camera, Camera.property_id == Property.id)
        .where(Camera.id == first_alert.camera_id)
    )
    property_obj = property_result.scalar_one_or_none()

    if property_obj is None or property_obj.neighbourhood_id is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    await _require_neighbourhood_membership(
        db,
        claims,
        property_obj.neighbourhood_id,
    )

    return _detail_for_incident(incident)
