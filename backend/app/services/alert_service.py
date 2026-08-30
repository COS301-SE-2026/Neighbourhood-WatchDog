import asyncio
import logging
import os

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
from datetime import datetime, timezone, timedelta, date as date_cls
from dateutil.relativedelta import relativedelta

from fastapi import HTTPException
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.neighbourhood_user import (
    NeighbourhoodRole,
    NeighbourhoodUser,
)
from app.models.property import Property
from app.models.camera import Camera
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.alert import (
    AlertClipUpdateRes,
    CreateInternalAlertRequest,
    InternalAlertCreateRes,
    UpdateAlertClipRequest,
    AlertRes
)
from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction, TargetEntity
from app.models.alert import Alert, DetectionType

from app.models.neighbourhood import Neighbourhood
from app.schemas.alert import AlertCreate, AlertMetricItem, AlertMetricsRes, TimeIntervalsEnum, TimePeriod, AlertFrequencyMetricsRes, NumberInPeriod, TrendGroupBy, TrendDirection, TrendBucket, TrendData, AlertResponse
from app.services.notification_service import _format_whatsapp_message, _notify_users
from app.models.user import User


logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
NO_DATABASE_SESSION = "No database session"
NOT_AUTHORISED = "Not authorised for this neighbourhood"
NOT_AUTHENTICATED = "Not authenticated"
ALERT_NOT_FOUND = "Alert not found"
CLIP_RETENTION_DAYS = int(os.getenv("CLIP_RETENTION_DAYS", "7"))
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
AWS_REGION = os.getenv("AWS_REGION", "af-south-1")


def _s3_client():
    return boto3.client(
        "s3",
        region_name="eu-north-1",
        endpoint_url="https://s3.eu-north-1.amazonaws.com",
        config=BotoConfig(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        ),
    )


def _clip_s3_key(alert: Alert, timestamp: datetime) -> str:
    return (
        f"clips/{alert.camera_id}/{timestamp:%Y/%m/%d}/"
        f"weapon_{timestamp:%Y%m%dT%H%M%SZ}_{alert.id}.mp4"
    )


def _neighbourhood_alert_stmt(neighbourhood_id: UUID):
    """Build the base alert query scoped through Camera → Property."""
    return (
        select(Alert)
        .join(Camera, Alert.camera_id == Camera.id)
        .join(Property, Camera.property_id == Property.id)
        .where(Property.neighbourhood_id == neighbourhood_id)
    )

async def _require_neighbourhood_membership(
    db: AsyncSession,
    claims: dict,
    neighbourhood_id: UUID,
    allowed_roles: set[NeighbourhoodRole] | None = None,
) -> NeighbourhoodUser:
    """Require the authenticated local user to belong to this neighbourhood."""

    try:
        user_id = UUID(claims["id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=401,
            detail=NOT_AUTHENTICATED,
        ) from exc

    stmt = select(NeighbourhoodUser).where(
        NeighbourhoodUser.user_id == user_id,
        NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
    )

    if allowed_roles is not None:
        stmt = stmt.where(NeighbourhoodUser.role.in_(allowed_roles))

    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail=NOT_AUTHORISED,
        )

    return membership

async def _get_neighbourhood_websocket_recipient_ids(
    db: AsyncSession,
    neighbourhood_id: UUID,
) -> list[str]:
    """Return WebSocket recipient IDs for members of a neighbourhood."""

    result = await db.execute(
        select(NeighbourhoodUser.user_id).where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
        )
    )

    return [str(user_id) for user_id in result.scalars().all()]


async def create_alert(db: AsyncSession, data: AlertCreate):
    """Create and persist an alert from an authenticated edge-agent detection."""
    try:
        alert = Alert(
            camera_id=data.camera_id,
            frame_timestamp=data.timestamp,
            detection_type=data.detection_type,
            confidence_score=data.confidence,
            thumbnail_url=data.thumbnail_url,
            processed=False,
        )
        db.add(alert)

        logger.info(
            "create_alert: Alert created: alert_id=%s, camera_id=%s, detection_type=%s",
            alert.id,
            alert.camera_id,
            alert.detection_type
        )

        await db.commit()
        await db.refresh(alert)


        from app.api.controllers.alert import broadcast

        if data.neighbourhood_id is not None:
            recipient_ids = await _get_neighbourhood_websocket_recipient_ids(
                db,
                data.neighbourhood_id,
            )

            await broadcast(
                recipient_ids,
                {
                    "event": "new_alert",
                    "alert_id": str(alert.id),
                    "camera_id": str(data.camera_id),
                    "detection_type": data.detection_type,
                    "confidence": data.confidence,
                },
            )
        else:
            logger.warning(
                "create_alert: skipped WebSocket broadcast because neighbourhood_id is missing; "
                "alert_id=%s",
                alert.id,
            )
            
        logger.info(
            "create_alert: Alert broadcast completed: alert_id=%s",
            alert.id
        )

        alert_response = AlertResponse(
            id=alert.id,
            camera_id=alert.camera_id,
            status=alert.status,
            created_at=alert.created_at,
        )

        return alert_response
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()

        logger.exception(
            "create_alert: Failed to create alert: camera_id=%s",
            data.camera_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alert: {str(e)}"
        )



def _build_alert_res(alert: Alert) -> AlertRes:
    """Convert an Alert database model into an AlertRes response object."""
    return AlertRes(
        id=alert.id,
        camera_id=alert.camera_id,
        frame_timestamp=alert.frame_timestamp,
        detection_type=(
            alert.detection_type.value
            if hasattr(alert.detection_type, "value")
            else str(alert.detection_type)
        ),
        confidence_score=alert.confidence_score,
        thumbnail_url=alert.thumbnail_url,
        clip_s3_key=alert.clip_s3_key,
        clip_expires_at=alert.clip_expires_at,
        processed=alert.processed,
        status=alert.status,
        resolved_by=alert.resolved_by,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
    )

async def acknowledge_alert_handler(alert_id, db: AsyncSession, claims: dict) -> AlertRes:
    """Acknowledge an open alert and record the responsible authorised user."""
    if not alert_id:
        logger.warning("acknowledge_alert_handler: no alert_id entered")
        raise HTTPException(400, "Alert id is required")
    _validate_db_and_claims(db, claims)

    try:
        result = await db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            logger.warning("acknowledge_alert: alert not found with alert_id=%s", alert_id)
            raise HTTPException(404, ALERT_NOT_FOUND)

        if alert.status != "OPEN":
            logger.warning("acknowledge_alert: alert not open with alert_id=%s", alert_id)
            raise HTTPException(409, "Alert is already acknowledged or resolved")

        neighbourhood_result = await db.execute(
            select(Property.neighbourhood_id)
            .join(Camera, Camera.property_id == Property.id)
            .where(Camera.id == alert.camera_id)
        )
        neighbourhood_id = neighbourhood_result.scalar_one_or_none()

        if neighbourhood_id is None:
            raise HTTPException(
                status_code=404,
                detail="Camera property is not assigned to a neighbourhood",
            )

        await _require_neighbourhood_membership(
            db,
            claims,
            neighbourhood_id,
        )

        resolver_id = UUID(claims["id"])

        old_values = {
            "status": alert.status,
            "resolved_by": str(alert.resolved_by) if alert.resolved_by else None,
            "resolved_at": (
                alert.resolved_at.isoformat() if alert.resolved_at else None
            ),
        }


        alert.status = "ACKNOWLEDGED"
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by = resolver_id

        await create_audit_log_item(
            db=db,
            user_id=resolver_id,
            action=AuditAction.UPDATE,
            target_entity_type=TargetEntity.ALERT,
            target_entity_id=alert.id,
            old_values=old_values,
            new_values={
                "status": alert.status,
                "resolved_by": (
                    str(alert.resolved_by) if alert.resolved_by else None
                ),
                "resolved_at": alert.resolved_at.isoformat(),
            },
        )

        await db.commit()

        alert_res = _build_alert_res(alert)

        try:
            from app.api.controllers.alert import broadcast

            if neighbourhood_id is not None:
                recipient_ids = await _get_neighbourhood_websocket_recipient_ids(
                    db,
                    neighbourhood_id,
                )

                await broadcast(
                    recipient_ids,
                    {
                        "event": "alert.acknowledged",
                        "payload": alert_res.model_dump(mode="json"),
                    },
                )
        except Exception:
            pass

        return alert_res
    except HTTPException as he:
        raise he
    except IntegrityError:
        logger.error("acknowledge_alert: failed to acknowledge with alert_id=%s due to integrity error", alert_id)
        await db.rollback()
        raise HTTPException(500, "Failed to acknowledge alert")

def _validate_db_and_claims(db: AsyncSession, claims: dict):
    if not db:
        logger.warning("acknowledge_alert_handler: no db entered")
        raise HTTPException(500, NO_DATABASE_SESSION)
    if not claims:
        logger.warning("acknowledge_alert_handler: no claims entered")
        raise HTTPException(401, NOT_AUTHENTICATED)

async def list_alerts_handler(
    neighbourhood_id,
    db: AsyncSession,
    claims: dict,
    status_filter: str | None = None,
    camera_id: UUID | None = None,
    detection_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[AlertRes], int]:
    """Return paginated alerts for an authorised neighbourhood with optional filters."""

    if not neighbourhood_id:
        raise HTTPException(400, "Neighbourhood id is required")
    if not db:
        raise HTTPException(500, NO_DATABASE_SESSION)
    if not claims:
        raise HTTPException(401, NOT_AUTHENTICATED)


    if start_date and end_date and start_date > end_date:
        logger.warning("list_alerts: start date and end date invalid for request for alerts for user with cognito_sub=%s", claims['sub'])
        raise HTTPException(400, "start_date must be less than end_date")

    neighbourhood_uuid = UUID(str(neighbourhood_id))

    await _require_neighbourhood_membership(
        db,
        claims,
        neighbourhood_uuid,
    )

    try:
        base_stmt = _neighbourhood_alert_stmt(neighbourhood_uuid)

        if status_filter:
            base_stmt = base_stmt.where(Alert.status == status_filter)
        if camera_id:
            base_stmt = base_stmt.where(Alert.camera_id == camera_id)
        if detection_type:
            base_stmt = base_stmt.where(Alert.detection_type == DetectionType(detection_type))
        if start_date:
            base_stmt = base_stmt.where(Alert.frame_timestamp >= start_date)
        if end_date:
            base_stmt = base_stmt.where(Alert.frame_timestamp <= end_date)

        count_result = await db.execute(
            select(func.count()).select_from(base_stmt.subquery())
        )
        total = count_result.scalar_one()

        stmt = (base_stmt.order_by(Alert.frame_timestamp.desc())
                .limit(limit)
                .offset(offset))

        result = await db.execute(stmt)
        alerts = result.scalars().all()

        return [_build_alert_res(a) for a in alerts], total
    except HTTPException as he:
        raise he
    except IntegrityError:
        logger.error("list_alerts: failed to fetch alerts for user with cognito_sub=%s due to integrity error", claims['sub'])
        await db.rollback()
        raise HTTPException(500, "Failed to list alerts")
    

async def get_response_metrics_handler(
        neighbourhood_id: UUID,
        db: AsyncSession,
        claims: dict,
        camera_id: UUID | None = None,
        officer_id: UUID | None = None
) -> AlertMetricsRes:
    """Calculate alert response metrics for an authorised neighbourhood."""

    _validate_db_and_claims(db, claims)

    neighbourhood_uuid = UUID(str(neighbourhood_id))

    await _require_neighbourhood_membership(
        db,
        claims,
        neighbourhood_uuid,
    )

    stmt = _neighbourhood_alert_stmt(neighbourhood_uuid)

    if camera_id:
        stmt = stmt.where(Alert.camera_id == camera_id)

    if officer_id:
        stmt = stmt.where(Alert.resolved_by == officer_id)

    result = await db.execute(stmt)
    alerts = result.scalars().all()


    items: list[AlertMetricItem] = []
    response_times: list[float] = []

    for alert in alerts:
        response_seconds = None
        if alert.resolved_at and alert.created_at:
            delta = alert.resolved_at - alert.created_at

            response_seconds = max(delta.total_seconds(), 0.0)
            response_times.append(response_seconds)

        display_status = "PENDING" if alert.status == "OPEN" else alert.status


        items.append(AlertMetricItem(
            alert_id=alert.id,
            camera_id=alert.camera_id,
            status=display_status,
            response_seconds=response_seconds,
            acknowledged_by=alert.resolved_by,
            created_at=alert.created_at

        ))
    
    avg = sum(response_times) / len(response_times) if response_times else None
    
    pending_count = sum(1 for a in alerts if a.status == "OPEN")

    acknowledged_count = sum(1 for a in alerts if a.status in ("ACKNOWLEDGED", "RESOLVED"))

    logger.info("get_response_metrics: successfully retrieved response metrics for user with cognito_sub=%s", claims['sub'])
    return AlertMetricsRes (
        total_alerts=len(alerts),
        acknowledged_count=acknowledged_count,
        pending_count=pending_count,
        average_response_seconds=avg,
        items=items
        
    )

INTERVAL_TO_TRUNC = {
    TimeIntervalsEnum.DAILY: "day",
    TimeIntervalsEnum.MONTHLY: "month",
    TimeIntervalsEnum.YEARLY: "year",
}

async def get_alert_frequency_metrics_handler(
    neighbourhood_id: UUID,
    db: AsyncSession,
    time_interval: TimeIntervalsEnum,
    time_period: TimePeriod,
    claims: dict
) -> AlertFrequencyMetricsRes:
    """Return grouped alert-frequency metrics for an authorised neighbourhood."""
    
    if not db:
        logger.warning("get_alert_frequency_metrics: failed due to no db")
        raise HTTPException(500, "No db")

    if not claims:
        logger.warning("get_alert_frequency_metrics: failed due to no claims")
        raise HTTPException(401, NOT_AUTHENTICATED)
    
    if not time_interval:
        logger.warning("get_alert_frequency_metrics: failed due to no time_interval")
        raise HTTPException(400, "No time interval provided")

    await _require_neighbourhood_membership(
        db,
        claims,
        neighbourhood_id,
    )
    
    start_date = None
    today = date_cls.today()

    if time_period:
        if time_period == TimePeriod.WEEK:
            start_date = today - timedelta(days=7)
        elif time_period == TimePeriod.MONTH:
            start_date = today - relativedelta(months=1)
        elif time_period == TimePeriod.THREE_MONTHS:
            start_date = today - relativedelta(months=3)
        elif time_period == TimePeriod.SIX_MONTHS:
            start_date = today - relativedelta(months=6)
        elif time_period == TimePeriod.YEAR:
            start_date = today - relativedelta(years=1)

    trunc_unit = INTERVAL_TO_TRUNC[time_interval]
    bucket = func.date_trunc(trunc_unit, Alert.frame_timestamp).label("bucket")

    stmt = (
        select(bucket, func.count(Alert.id).label("count"))
        .join(Camera, Alert.camera_id == Camera.id)
        .join(Property, Camera.property_id == Property.id)
        .where(Property.neighbourhood_id == UUID(str(neighbourhood_id)))
    )


    if start_date:
        stmt = stmt.where(Alert.frame_timestamp > start_date)

    stmt = stmt.group_by(bucket).order_by(bucket)

    result = await db.execute(stmt)
    rows = result.all()

    period_arr = []
    count_arr = []

    for row in rows:
        period_arr.append(row.bucket)
        count_arr.append(row.count)

    data = NumberInPeriod(
        period=period_arr,
        count=count_arr
    )

    logger.info("get_alert_frequency_metrics: successfully fetched alert frequency metrics for user with cognito_sub=%s", claims['sub'])
    return AlertFrequencyMetricsRes(
        status=200,
        data=data
    )
    



def _resolve_start_date(time_period: TimePeriod | None) -> date_cls | None:
    """Convert a requested reporting period into its inclusive start date."""

    if not time_period:
        return None
    

    today = date_cls.today()

    if time_period == TimePeriod.WEEK:
        return today - timedelta(days=7)
    elif time_period == TimePeriod.MONTH:
        return today - relativedelta(months=1)
    elif time_period == TimePeriod.THREE_MONTHS:
        return today - relativedelta(months=3)
    elif time_period == TimePeriod.SIX_MONTHS:
        return today - relativedelta(months=6)
    elif time_period == TimePeriod.YEAR:
        return today - relativedelta(years=1)
    

    return None



def _compute_trend_direction(buckets: list[TrendBucket]) -> TrendDirection:
    """Determine whether alert counts are increasing, decreasing, or stable."""
    if len(buckets) < 2:
        return TrendDirection.STABLE


    middle = len(buckets) // 2
    first_half = sum(b.count for b in buckets[:middle])
    second_half = sum(b.count for b in buckets[middle:])

    if (first_half > second_half):
        return TrendDirection.DOWN
    
    if (first_half < second_half):
        return TrendDirection.UP
    
    return TrendDirection.STABLE


async def get_trends_handler(
    neighbourhood_id: UUID,
    db: AsyncSession,
    claims: dict,
    group_by: TrendGroupBy = TrendGroupBy.DAY,
    time_period: TimePeriod = TimePeriod.MONTH,
    incident_type: str | None = None,
    camera_id: UUID | None = None,
) -> TrendData:
    """Return grouped alert trends and their overall direction for a neighbourhood."""

    if not db:
        logger.warning("get_trends: failed to get trends due to no database")
        raise HTTPException(500, NO_DATABASE_SESSION)
    
    if not claims:
        logger.warning("get_trends: failed to get trends due to no claims")
        raise HTTPException(401, NOT_AUTHENTICATED)

    await _require_neighbourhood_membership(
        db,
        claims,
        neighbourhood_id,
    )
    
    start_date = _resolve_start_date(time_period)

    bucket = func.date_trunc(group_by.value, Alert.frame_timestamp).label("bucket")

    stmt = (
        select(bucket, func.count(Alert.id).label("count"))
        .join(Camera, Alert.camera_id == Camera.id)
        .join(Property, Camera.property_id == Property.id)
        .where(Property.neighbourhood_id == neighbourhood_id)
    )
    
    if start_date:
        stmt = stmt.where(Alert.frame_timestamp > start_date)

    if camera_id:
        stmt = stmt.where(Alert.camera_id == camera_id)
    
    if incident_type:
        stmt = stmt.where(Alert.detection_type == DetectionType(incident_type))

    stmt = stmt.group_by(bucket).order_by(bucket)

    try:
        result = await db.execute(stmt)
        rows = result.all()
    except IntegrityError:
        logger.error("get_trends: failed due to integrity error for request from user with cognito_sub=%s", claims['sub'])
        await db.rollback()
        raise HTTPException(500, "Failed to fetch trend data")
    
    
    buckets = [TrendBucket(period=row.bucket, count=row.count) for row in rows]
    total_count = sum(b.count for b in buckets)
    trend_direction = _compute_trend_direction(buckets)

    logger.info("get_trends: successfully retrieved trend data for user with cognito_sub=%s", claims['sub'])
    return TrendData(
        buckets=buckets,
        total_count=total_count,
        trend_direction=trend_direction
    )


async def broadcast_neighbourhood_alert_service(alert_id: UUID, db: AsyncSession, claims: dict):
    """Broadcast an alert and notify eligible residents in its neighbourhood."""
    
    from app.api.controllers.alert import broadcast

    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        logger.warning("broadcast_neighbourhood_alert_service: could not find alert with alert_id=%s", alert_id)
        raise HTTPException(status_code=404, detail=ALERT_NOT_FOUND)

    result = await db.execute(
        select(Camera)
        .options(joinedload(Camera.property)) # to load the property so the neighbourhood id can be accessed through that
        .where(Camera.id == alert.camera_id)
    )
    camera = result.scalar_one_or_none()
    if not camera:
        logger.warning("broadcast_neighbourhood_alert_service: could not find camera linked to alert with alert_id=%s", alert_id)
        raise HTTPException(status_code=404, detail="Camera not found for alert")

    neighbourhood_id = camera.property.neighbourhood_id #has to access the neighbourhood via the camera's property

    if not neighbourhood_id:
        logger.warning("broadcast_neighbourhood_alert_service: property with property_id=%s not linked to neighbourhood", camera.property_id)

    if neighbourhood_id is None:
        raise HTTPException(
            status_code=404,
            detail="Camera property is not assigned to a neighbourhood",
        )

    await _require_neighbourhood_membership(
        db,
        claims,
        neighbourhood_id,
        allowed_roles={NeighbourhoodRole.NEIGHBOURHOOD_ADMIN},
    )

    result = await db.execute(
        select(Neighbourhood).where(
            Neighbourhood.id == neighbourhood_id
        )
    )

    neighbourhood = result.scalar_one_or_none()
    if not neighbourhood:
        logger.warning("broadcast_neighbourhood_alert_service: could not find neighbourhoodcamera linked to alert with alert_id=%s", alert_id)
        raise HTTPException(status_code=404, detail="Neighbourhood not found")

    detection_type = alert.detection_type.value \
    if hasattr(alert.detection_type, "value") \
    else str(alert.detection_type)

    alert_res = _build_alert_res(alert)
    recipient_ids = await _get_neighbourhood_websocket_recipient_ids(
        db,
        neighbourhood_id,
    )

    await broadcast(
        recipient_ids,
        {
            "event": "alert.broadcast",
            "payload": alert_res.model_dump(mode="json"),
        },
    )

    result = await db.execute(
        select(User)
        .join(
            NeighbourhoodUser,
            NeighbourhoodUser.user_id == User.id,
        )
        .where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
            NeighbourhoodUser.role.in_(
                [
                    NeighbourhoodRole.RESIDENT,
                    NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
                ]
            ),
        )
    )

    residents = result.scalars().all()

    timestamp_str = alert.frame_timestamp.strftime("%d %b %Y, %H:%M:%S")
    whatsapp_message = _format_whatsapp_message("CRITICAL", detection_type, camera.name, timestamp_str)
    await _notify_users(db, alert.id, residents, whatsapp_message, detection_type, camera, "CRITICAL") #imma need to store val to know if failed or not

    admin_user_id = UUID(claims["id"])
    
    await create_audit_log_item(
        db=db,
        user_id=admin_user_id,
        action=AuditAction.UPDATE,
        target_entity_type=TargetEntity.ALERT,
        target_entity_id=alert.id,
        old_values={
            "broadcast": False,
        },
        new_values={
            "broadcast": True,
            "neighbourhood_id": str(neighbourhood_id),
        },
    )

    await db.commit()

async def create_alert_for_agent_handler(body: CreateInternalAlertRequest, db:AsyncSession, credential: EdgeAgentCredential) -> InternalAlertCreateRes:
    """Create an alert for a camera owned by the authenticated edge agent's property."""

    label_map = {
        "gun": DetectionType.WEAPON_DETECTED,
        "knife": DetectionType.WEAPON_DETECTED,
        "grenade": DetectionType.WEAPON_DETECTED,
        "explosion": DetectionType.WEAPON_DETECTED
    }

    try:
        det_type = DetectionType(body.detection_type.upper())
    except ValueError:
        det_type = label_map.get(body.detection_type.lower(), DetectionType.WEAPON_DETECTED)

    try:
        camera_id = UUID(body.camera_id)
    except ValueError:
        logger.warning("internal create_alert: malformed camera_id=%s", body.camera_id)
        raise HTTPException(status_code=400, detail="camera_id is not a valid UUID")

    if body.frame_timestamp:
        try:
            frame_timestamp = datetime.fromisoformat(body.frame_timestamp)
        except ValueError:
            logger.warning("internal create_alert: malformed frame_timestamp=%s", body.frame_timestamp)
            raise HTTPException(status_code=400, detail="frame_timestamp is not a valid ISO datetime")
    else:
        frame_timestamp = datetime.now(timezone.utc)

    try:

        stmt = select(Camera).where(Camera.id == body.camera_id)
        result = await db.execute(stmt)
        camera: Camera | None = result.scalar_one_or_none()

        if not camera:
            logger.warning("internal create_alert: no camera found for camera_id=%s", body.camera_id)
            raise HTTPException(status_code=404,detail=f"Camera {body.camera_id} not found")

        
        alert = Alert(
            camera_id=camera_id,
            frame_timestamp= frame_timestamp,
            detection_type=det_type,
            confidence_score=body.confidence_score,
            thumbnail_url=body.thumbnail_url,
            processed=True,
            status="OPEN"
        )

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        logger.info(
            "Internal alert created: alert_id=%s, camera_id=%s, detection_type=%s",
            alert.id,
            alert.camera_id,
            alert.detection_type,
        )

        return InternalAlertCreateRes(alert_id=alert.id)

    
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        logger.exception(
            "Unexpected failure while creating an internal alert for camera_id=%s.",
            camera_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to create alert",
        )


async def update_alert_clip_for_agent_handler(alert_id: str, body: UpdateAlertClipRequest, credential: EdgeAgentCredential, db: AsyncSession) -> AlertClipUpdateRes:
    """Update clip metadata for an alert owned by the authenticated edge agent's property."""

    try:
        alert_uuid = UUID(alert_id)
    except ValueError:
        logger.warning("internal update_clip: malformed alert_id=%s", alert_id)
        raise HTTPException(status_code=400, detail="alert_id is not a valid UUID")

    try:
        clip_expires_at = datetime.fromisoformat(body.clip_expires_at)
    except ValueError:
        logger.warning("internal update_clip: malformed clip_expires_at=%s", body.clip_expires_at)
        raise HTTPException(status_code=400, detail="clip_expires_at is not a valid ISO datetime")

    try:
        stmt = select(Alert).where(Alert.id == alert_uuid)
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()

        if not alert:
            logger.warning("internal update_clip: alert with alert id=%s not found.", alert_id)
            raise HTTPException(
                status_code=404,
                detail=ALERT_NOT_FOUND
            )

        alert.clip_s3_key = body.clip_s3_key
        alert.clip_expires_at = clip_expires_at

        await db.commit()
        await db.refresh(alert)

        logger.info("internal update_clip: clip with alert_id=%s successfully updated.", alert_id)
        return AlertClipUpdateRes(
            alert_id=alert.id,
            clip_s3_key=alert.clip_s3_key,
            clip_expires_at=alert.clip_expires_at,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("internal update_clip: unexpected error updating clip for alert_id=%s", alert_id)
        raise


async def upload_alert_clip_for_agent_handler(
    alert_id: str,
    clip_bytes: bytes,
    content_type: str | None,
    credential: EdgeAgentCredential,
    db: AsyncSession,
) -> AlertClipUpdateRes:
    """Upload an Edge Agent clip to backend-owned S3 storage and link it to its alert."""
    if not S3_BUCKET_NAME:
        raise HTTPException(status_code=503, detail="Clip storage has not been configured.")

    if not clip_bytes:
        raise HTTPException(status_code=400, detail="The uploaded clip is empty.")

    if len(clip_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Clip exceeds the 50 MiB upload limit.")

    try:
        alert_uuid = UUID(alert_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="alert_id is not a valid UUID") from error

    stmt = (
        select(Alert)
        .join(Camera, Alert.camera_id == Camera.id)
        .where(
            Alert.id == alert_uuid,
            Camera.property_id == credential.property_id,
        )
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail=ALERT_NOT_FOUND)

    timestamp = datetime.now(timezone.utc)
    s3_key = _clip_s3_key(alert, timestamp)
    expires_at = timestamp + timedelta(days=CLIP_RETENTION_DAYS)
    uploaded = False

    try:
        await asyncio.to_thread(
            _s3_client().put_object,
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=clip_bytes,
            ContentType=content_type or "video/mp4",
            ServerSideEncryption="AES256",
        )
        uploaded = True

        alert.clip_s3_key = s3_key
        alert.clip_expires_at = expires_at
        await db.commit()
        await db.refresh(alert)

        logger.info(
            "Uploaded and linked clip for alert %s: s3://%s/%s",
            alert.id,
            S3_BUCKET_NAME,
            s3_key,
        )
        return AlertClipUpdateRes(
            alert_id=alert.id,
            clip_s3_key=alert.clip_s3_key,
            clip_expires_at=alert.clip_expires_at,
        )
    except (BotoCoreError, ClientError) as error:
        await db.rollback()
        logger.exception("S3 upload failed for alert %s", alert_id)
        raise HTTPException(status_code=503, detail="Could not store clip in S3.") from error
    except Exception:
        await db.rollback()
        logger.exception("Clip upload/link failed for alert %s", alert_id)
        raise
    finally:
        if uploaded and alert.clip_s3_key != s3_key:
            try:
                await asyncio.to_thread(
                    _s3_client().delete_object,
                    Bucket=S3_BUCKET_NAME,
                    Key=s3_key,
                )
            except Exception:
                logger.exception("Could not remove orphaned S3 clip %s", s3_key)


async def get_alert_for_agent(
    alert_id: str,
    credential: EdgeAgentCredential,
    db: AsyncSession,
) -> Alert | None:
    try:
        alert_uuid = UUID(alert_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="alert_id is not a valid UUID") from error

    stmt = (
        select(Alert)
        .join(Camera, Alert.camera_id == Camera.id)
        .where(
            Alert.id == alert_uuid,
            Camera.property_id == credential.property_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()