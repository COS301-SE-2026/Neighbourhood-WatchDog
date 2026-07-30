from datetime import datetime, timezone, timedelta, date as date_cls
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.detection_event import DetectionEvent
from app.schemas.alert import AlertCreate, AlertMetricItem, AlertMetricsRes, TimeIntervalsEnum, TimePeriod, AlertFrequencyMetricsRes, NumberInPeriod, TrendGroupBy, TrendDirection, TrendBucket, TrendData
from fastapi import HTTPException

from app.models.user import User
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.core.database import DbSession
from app.models.camera import Camera
from app.schemas.alert import AlertRes

from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction
from uuid import UUID

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
NO_DATABASE_SESSION = "No database session"
NOT_AUTHORISED = "Not authorised for this neighbourhood"

async def create_alert(db: Session, data: AlertCreate):
    try:
        detection_event = DetectionEvent(
            camera_id=data.camera_id,
            frame_timestamp=data.timestamp,
            detection_type=data.detection_type,
            confidence_score=data.confidence,
            thumbnail_url=data.thumbnail_url,
            processed=False,
        )
        db.add(detection_event)
        db.flush()

        alert = Alert(
            camera_id=data.camera_id,
            detection_event_id=detection_event.id,
            status="OPEN",
        )

        db.add(alert)
        db.flush() 
        db.commit()
        db.refresh(alert)

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
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alert: {str(e)}"
        )



def _build_alert_res(alert: Alert) -> AlertRes:
    event = alert.detection_event
    return AlertRes(
        id=alert.id,
        camera_id=alert.camera_id,
        detection_event_id=alert.detection_event_id,
        status=alert.status,
        resolved_by=alert.resolved_by,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
        detection_type=event.detection_type if event else None,
        confidence_score=event.confidence_score if event else None,
        thumbnail_url=event.thumbnail_url if event else None,
    )


async def acknowledge_alert_handler(alert_id, db: DbSession, claims: dict) -> AlertRes:
    if not alert_id:
        raise HTTPException(400, "Alert id is required")
    if not db:
        raise HTTPException(500, NO_DATABASE_SESSION)
    if not claims:
        raise HTTPException(401, "Not authenticated")

    role = claims.get("custom:role")
    if role not in ["SECURITY_OFFICER", "NEIGHBOURHOOD_ADMIN"]:
        raise HTTPException(403, "Insufficient permissions")

    try:
        alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
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
            resolver = db.execute(
                select(User).where(User.cognito_sub == user_id_str)
            ).scalar_one_or_none()

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
            target_entity_type="Alert",
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

        db.commit()

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
        db.rollback()
        raise HTTPException(500, "Failed to acknowledge alert")


async def list_alerts_handler(
    neighbourhood_id,
    db: DbSession,
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
            .join(DetectionEvent, Alert.detection_event_id == DetectionEvent.id)
            .where(Camera.neighbourhood_id == UUID(str(neighbourhood_id)))
        )

        if status_filter:
            base_stmt = base_stmt.where(Alert.status == status_filter)
        if camera_id:
            base_stmt = base_stmt.where(Alert.camera_id == camera_id)
        if detection_type:
            base_stmt = base_stmt.where(DetectionEvent.detection_type == detection_type)
        if start_date:
            base_stmt = base_stmt.where(Alert.created_at >= start_date)
        if end_date:
            base_stmt = base_stmt.where(Alert.created_at <= end_date)

        total = db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()

        stmt = (base_stmt.order_by(Alert.created_at.desc())
                .limit(limit)
                .offset(offset))

        alerts = db.execute(stmt).scalars().all()
        return [_build_alert_res(a) for a in alerts], total
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to list alerts")
    

def get_response_metrics_handler(
        neighbourhood_id: UUID,
        db: DbSession,
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

    alerts = db.execute(stmt).scalars().all()


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
    db: DbSession,
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
    bucket = func.date_trunc(trunc_unit, Alert.created_at).label("bucket")

    stmt = (
        select(bucket, func.count(Alert.id).label("count"))
        .join(Camera, Alert.camera_id == Camera.id)
        .where(Camera.neighbourhood_id == UUID(str(neighbourhood_id)))
    )

    print(start_date)

    if start_date:
        stmt = stmt.where(Alert.created_at > start_date)

    stmt = stmt.group_by(bucket).order_by(bucket)

    rows = db.execute(stmt).all()

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


async def get_trends_handler(neighbourhood_id: UUID, db: DbSession, claims: dict, group_by: TrendGroupBy=TrendGroupBy.DAY,
                             time_period: TimePeriod=TimePeriod.MONTH, incident_type: str | None=None, camera_id=UUID) -> TrendData:
    
    if not db:
        raise HTTPException(500, NO_DATABASE_SESSION)
    
    if not claims:
        raise HTTPException(401, "Not authenticated")
    

    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, NOT_AUTHORISED)
    

    start_date = _resolve_start_date(time_period)


    bucket = func.date_trunc(group_by.value, Alert.created_at).label("bucket")


    stmt = (
        select(bucket, func.count(Alert.id).label("count"))
        .join(Camera, Alert.camera_id == Camera.id)
        .join(DetectionEvent, Alert.detection_event_id == DetectionEvent.id)
        .where(Camera.neighbourhood_id == UUID(str(neighbourhood_id)))
    )

    
    if start_date:
        stmt = stmt.where(Alert.created_at > start_date)


    if camera_id:
        stmt = stmt.where(Alert.camera_id == camera_id)

    
    if incident_type:
        stmt = stmt.where(DetectionEvent.detection_type == incident_type)


    stmt = stmt.group_by(bucket).order_by(bucket)



    try:
        rows = db.execute(stmt).all()
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to fetch trend data")
    


    buckets = [TrendBucket(period=row.bucket, count=row.count) for row in rows]
    total_count = sum(b.count for b in buckets)
    trend_direction = _compute_trend_direction(buckets)





    return TrendData(
        
        buckets=buckets,
        total_count=total_count,
        trend_direction=trend_direction


    )