from datetime import datetime, timezone, timedelta, date as date_cls
from dateutil.relativedelta import relativedelta

from app.models.neighbourhood import Neighbourhood
from app.schemas.alert import AlertCreate, AlertMetricItem, AlertMetricsRes, TimeIntervalsEnum, TimePeriod, AlertFrequencyMetricsRes, NumberInPeriod, TrendGroupBy, TrendDirection, TrendBucket, TrendData
from fastapi import HTTPException

from app.models.user import User, UserRole
from sqlalchemy import or_, select, func
from sqlalchemy.exc import IntegrityError

from app.models.camera import Camera
from app.schemas.alert import AlertRes

from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction, TargetEntity
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert import Alert, DetectionType

from app.services.notification_service import _format_whatsapp_message, _notify_users

import logging

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
NO_DATABASE_SESSION = "No database session"
NOT_AUTHORISED = "Not authorised for this neighbourhood"

async def create_alert(db: AsyncSession, data: AlertCreate):
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

        await db.commit()
        await db.refresh(alert)


        from app.api.controllers.alert import broadcast
        await broadcast(str(data.neighbourhood_id), {
            "event": "new_alert",
            "alert_id": str(alert.id),
            "camera_id": str(data.camera_id),
            "detection_type": data.detection_type,
            "confidence": data.confidence,
        })

        return alert
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alert: {str(e)}"
        )



def _build_alert_res(alert: Alert) -> AlertRes:
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
    if not alert_id:
        raise HTTPException(400, "Alert id is required")
    if not db:
        raise HTTPException(500, NO_DATABASE_SESSION)
    if not claims:
        raise HTTPException(401, "Not authenticated")

    role = claims.get("custom:role")
    if role not in ["SECURITY_OFFICER", "NEIGHBOURHOOD_ADMIN", "RESIDENT"]:
        raise HTTPException(403, "Insufficient permissions")

    try:
        result = await db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(404, "Alert not found")

        if alert.status != "OPEN":
            raise HTTPException(409, "Alert is already acknowledged or resolved")

        user_id_str = claims.get("sub") or claims.get("custom:sub")

        old_values = {
            "status": alert.status,
            "resolved_by": str(alert.resolved_by) if alert.resolved_by else None,
            "resolved_at": (
                alert.resolved_at.isoformat() if alert.resolved_at else None
            ),
        }

        resolver_id = None

        if user_id_str:
            result = await db.execute(
                select(User).where(User.cognito_sub == user_id_str)
            )
            resolver = result.scalar_one_or_none()

            if resolver is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authenticated user does not have a local WatchDog profile.",
                )

            resolver_id = resolver.id

        alert.status = "ACKNOWLEDGED"
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by = resolver_id

        create_audit_log_item(
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

            await broadcast(
                neighbourhood_id=str(claims.get("custom:neighbourhood_id")),
                message={"event": "alert.acknowledged", "payload": alert_res.model_dump(mode="json")},
            )
        except Exception:
            pass

        return alert_res
    except HTTPException as he:
        raise he
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Failed to acknowledge alert")


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
    if not neighbourhood_id:
        raise HTTPException(400, "Neighbourhood id is required")
    if not db:
        raise HTTPException(500, NO_DATABASE_SESSION)
    if not claims:
        raise HTTPException(401, "Not authenticated")

    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, NOT_AUTHORISED)

    if start_date and end_date and start_date > end_date:
        raise HTTPException(400, "start_date must be less than end_date")

    try:
        base_stmt = (
            select(Alert)
            .join(Camera, Alert.camera_id == Camera.id)
            .where(Camera.neighbourhood_id == UUID(str(neighbourhood_id)))
        )

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
        await db.rollback()
        raise HTTPException(500, "Failed to list alerts")
    

async def get_response_metrics_handler(
        neighbourhood_id: UUID,
        db: AsyncSession,
        claims: dict,
        camera_id: UUID | None = None,
        officer_id: UUID | None = None
) -> AlertMetricsRes:
    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, NOT_AUTHORISED)
    

    stmt = (
        select(Alert).join(
            Camera, 
            Alert.camera_id == Camera.id
        ).where(
            Camera.neighbourhood_id == neighbourhood_id
        )
    )

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
    
    if not db:
        raise HTTPException(500, "No db")

    if not claims:
        raise HTTPException(401, "Not authenticated")
    
    if not time_interval:
        raise HTTPException(400, "No time interval provided")
    
    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, NOT_AUTHORISED)
    
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
        .where(Camera.neighbourhood_id == UUID(str(neighbourhood_id)))
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

    return AlertFrequencyMetricsRes(
        status=200,
        data=data
    )
    



def _resolve_start_date(time_period: TimePeriod | None) -> date_cls | None:


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
    
    if not db:
        raise HTTPException(500, NO_DATABASE_SESSION)
    
    if not claims:
        raise HTTPException(401, "Not authenticated")
    

    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, NOT_AUTHORISED)
    

    start_date = _resolve_start_date(time_period)


    bucket = func.date_trunc(group_by.value, Alert.frame_timestamp).label("bucket")


    stmt = (
        select(bucket, func.count(Alert.id).label("count"))
        .join(Camera, Alert.camera_id == Camera.id)
        .where(Camera.neighbourhood_id == neighbourhood_id)
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
        await db.rollback()
        raise HTTPException(500, "Failed to fetch trend data")
    


    buckets = [TrendBucket(period=row.bucket, count=row.count) for row in rows]
    total_count = sum(b.count for b in buckets)
    trend_direction = _compute_trend_direction(buckets)





    return TrendData(
        
        buckets=buckets,
        total_count=total_count,
        trend_direction=trend_direction


    )

async def broadcast_neighbourhood_alert_service(alert_id: UUID, db: AsyncSession, claims: dict):
    from app.api.controllers.alert import broadcast

    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    result = await db.execute(
        select(Camera).where(Camera.id == alert.camera_id)
    )
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found for alert")

    neighbourhood_id = camera.neighbourhood_id

    result = await db.execute(
        select(Neighbourhood).where(
            Neighbourhood.id == camera.neighbourhood_id
        )
    )
    neighbourhood = result.scalar_one_or_none()
    if not neighbourhood:
        raise HTTPException(status_code=404, detail="Neighbourhood not found")

    detection_type = alert.detection_type.value \
    if hasattr(alert.detection_type, "value") \
    else str(alert.detection_type)

    alert_res = _build_alert_res(alert)
    await broadcast(
        neighbourhood_id=str(neighbourhood_id),
        message={"event": "alert.broadcast", "payload": alert_res.model_dump(mode="json")},
    )

    result = await db.execute(
        select(User).where(
            User.neighbourhood_id == neighbourhood_id,
            or_(
                User.role == UserRole.RESIDENT,
                User.role == UserRole.NEIGHBOURHOOD_ADMIN,
            ),
        )
    )
    residents = result.scalars().all()

    timestamp_str = alert.frame_timestamp.strftime("%d %b %Y, %H:%M:%S")
    whatsapp_message = _format_whatsapp_message("CRITICAL", detection_type, camera.name, timestamp_str)
    await _notify_users(db, alert.id, residents, whatsapp_message, detection_type, camera, "CRITICAL") #imma need to store val to know if failed or not

    result = await db.execute(
        select(User.id).where(User.cognito_sub == claims.get("sub"))
    )
    admin_user_id = result.scalar_one_or_none()
    if not admin_user_id:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    create_audit_log_item(
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