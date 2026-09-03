import asyncio
import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.authorization import Claims, NeighbourhoodMemberClaims
from app.auth.dependencies import get_authenticated_edge_agent
from app.core.database import DbSession, get_db
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.alert import (
    AcknowledgeAlertRes,
    AlertCreate,
    AlertFrequencyMetricsRes,
    AlertMetricsRes,
    AlertResponse,
    BroadcastAlertReq,
    ListAlertsRes,
    Pagination,
    TimeIntervalsEnum,
    TimePeriod,
    TrendGroupBy,
    TrendResponse,
)
from app.services import alert_service
from app.services.alert_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    acknowledge_alert_handler,
    broadcast_neighbourhood_alert_service,
    get_alert_frequency_metrics_handler,
    get_response_metrics_handler,
    get_trends_handler,
    list_alerts_handler,
    list_property_alerts_handler,
)
from app.services import alert_service
from app.schemas.alert import (
    AlertMetricsRes,
    AlertFrequencyMetricsRes,
    TimeIntervalsEnum,
    TimePeriod,
    TrendResponse,
    TrendGroupBy,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])

_connections: dict[str, set[WebSocket]] = {}
#TODO: NOTHING HERE SHOULD BE PUBLIC, NEED TO MAKE EVERYTHING PRIVATE 

def _get_bucket(user_id: str) -> set[WebSocket]:
    if user_id not in _connections:
        _connections[user_id] = set()
    return _connections[user_id]


def register_connection(user_id: str, websocket: WebSocket) -> None:
    _get_bucket(user_id).add(websocket)


def remove_connection(user_id: str, websocket: WebSocket) -> None:
    connections = _connections.get(user_id)

    if not connections:
        return

    connections.discard(websocket)

    if not connections:
        _connections.pop(user_id, None)


async def broadcast(user_ids: list[str], message: dict) -> None:
    payload = json.dumps(message)

    for user_id in user_ids:
        connections = _connections.get(user_id, set())
        dead: set[WebSocket] = set()

        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)

        for ws in dead:
            connections.discard(ws)



@router.get("/metrics", response_model=AlertMetricsRes)
async def get_alert_metrics(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: NeighbourhoodMemberClaims,
    camera_id: UUID | None = None,
    officer_id: UUID | None = None,
):
    """This will rep the time metrics for the alerts in the neighbourhood; can be filtered by camera and officer"""
    return await get_response_metrics_handler(neighbourhood_id, db, claims, camera_id, officer_id)

@router.get("/frequency-metrics", response_model=AlertFrequencyMetricsRes)
async def get_alert_frequency_metrics(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: NeighbourhoodMemberClaims,
    time_interval: TimeIntervalsEnum = TimeIntervalsEnum.DAILY,
    time_period: TimePeriod = TimePeriod.WEEK
):
    """Responds with number of alerts received with the neighbourhood. time_interval refers to the grouping of the numbers while time period refers to how far back the data should go."""
    return await get_alert_frequency_metrics_handler(
        neighbourhood_id=neighbourhood_id,
        db=db,
        time_interval=time_interval,
        time_period=time_period,
        claims=claims,
    )

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate, 
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await alert_service.create_alert(db, alert)

@router.post("/dev/broadcast") #TODO: remove before production
async def dev_broadcast_alert(data: dict):
    """Dev-only: broadcast alert without DB. Remove before production."""
    await broadcast([], {
        "event": "new_alert",
        "camera_id": data.get("camera_id", "unknown"),
        "detection_type": data.get("detection_type", "HUMAN_PRESENCE"),
        "confidence": data.get("confidence", 0.0),
    })
    return {"status": "broadcasted"}



@router.get("/trends", response_model=TrendResponse)
async def get_alert_trends(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: NeighbourhoodMemberClaims,
    group_by: TrendGroupBy=TrendGroupBy.DAY,
    time_period: TimePeriod=TimePeriod.MONTH, 
    incident_type: str | None=None, 
    camera_id: UUID | None=None


):
    data = await get_trends_handler(
        neighbourhood_id=neighbourhood_id,
        db=db,
        claims=claims,
        group_by=group_by,
        time_period=time_period, 
        incident_type=incident_type, 
        camera_id=camera_id 

    )
    return TrendResponse(status=200, data=data, message="Alert trends recieved successfully")


@router.get(
    "/property/{property_id}",
    response_model=ListAlertsRes,
    summary="List alerts for a property",
)
async def list_property_alerts(
    property_id: UUID,
    db: DbSession,
    claims: Claims,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    camera_id: Annotated[UUID | None, Query()] = None,
    detection_type: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    results, total = await list_property_alerts_handler(
        property_id=property_id,
        db=db,
        claims=claims,
        status_filter=status_filter,
        camera_id=camera_id,
        detection_type=detection_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return ListAlertsRes(
        status=200,
        data=results,
        pagination=Pagination(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.get(
    "/{neighbourhood_id}",
    response_model=ListAlertsRes,
    summary="List alerts for a neighbourhood",
)
async def list_alerts(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: NeighbourhoodMemberClaims,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    camera_id: Annotated[UUID | None, Query()] = None,
    detection_type: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None,  Query()] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    results, total = await list_alerts_handler(
        str(neighbourhood_id), 
        db, 
        claims, 
        status_filter=status_filter, 
        camera_id=camera_id, 
        detection_type=detection_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,)
    return ListAlertsRes(
        status=200, 
        data=results,
        pagination=Pagination(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ))


@router.patch("/{alert_id}/acknowledge", response_model=AcknowledgeAlertRes, summary="Acknowledge an alert")
async def acknowledge_alert(
    alert_id: UUID,
    db: DbSession,
    claims: Claims,
):
    result = await acknowledge_alert_handler(alert_id, db, claims)
    return AcknowledgeAlertRes(status=200, data=result)


@router.websocket("/ws")
async def alert_websocket(
    neighbourhood_id: UUID,
    websocket: WebSocket,
    claims: Claims
):
   
    user_id = claims["id"]

    await websocket.accept()
    register_connection(user_id, websocket)

    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"event": "ping"}))
    except Exception:
        pass
    finally:
        remove_connection(str(neighbourhood_id), websocket)

@router.post("/broadcast")
async def broadcast_neighbourhood_alert(
    req: BroadcastAlertReq,
    db: DbSession, 
    claims: Claims
    ):

    

    await broadcast_neighbourhood_alert_service(req.alert_id, db, claims)