import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import DbSession, get_db
from app.schemas.alert import AcknowledgeAlertRes, AlertCreate, AlertRes, AlertResponse, ListAlertsRes
from app.services.alert_service import acknowledge_alert_handler, list_alerts_handler
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])

_connections: dict[str, set[WebSocket]] = {}


def _get_bucket(neighbourhood_id: str) -> set[WebSocket]:
    if neighbourhood_id not in _connections:
        _connections[neighbourhood_id] = set()
    return _connections[neighbourhood_id]


def register_connection(neighbourhood_id: str, websocket: WebSocket) -> None:
    _get_bucket(neighbourhood_id).add(websocket)


def remove_connection(neighbourhood_id: str, websocket: WebSocket) -> None:
    _get_bucket(neighbourhood_id).discard(websocket)


async def broadcast(neighbourhood_id: str, message: dict) -> None:
    connections = _get_bucket(neighbourhood_id)
    dead: set[WebSocket] = set()

    payload = json.dumps(message)
    for ws in connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)

    for ws in dead:
        connections.discard(ws)


@router.post("/", response_model=AlertResponse)
async def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    return await alert_service.create_alert(db, alert)

@router.post("/dev/broadcast")
async def dev_broadcast_alert(data: dict):
    """Dev-only: broadcast alert without DB. Remove before production."""
    neighbourhood_id = data.get("neighbourhood_id", "10000000-0000-0000-0000-000000000001")
    await broadcast(str(neighbourhood_id), {
        "event": "new_alert",
        "camera_id": data.get("camera_id", "unknown"),
        "detection_type": data.get("detection_type", "HUMAN_PRESENCE"),
        "confidence": data.get("confidence", 0.0),
    })
    return {"status": "broadcasted"}

@router.get(
    "/{neighbourhood_id}",
    response_model=ListAlertsRes,
    summary="List alerts for a neighbourhood",
)
async def list_alerts(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: dict = Depends(get_current_user),
    status_filter: str | None = Query(default=None, alias="status"),
):
    results = await list_alerts_handler(str(neighbourhood_id), db, claims, status_filter)
    return ListAlertsRes(status=200, data=results)


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AcknowledgeAlertRes,
    summary="Acknowledge an alert",
)
async def acknowledge_alert(
    alert_id: UUID,
    db: DbSession,
    claims: dict = Depends(get_current_user),
):
    result = await acknowledge_alert_handler(alert_id, db, claims)
    return AcknowledgeAlertRes(status=200, data=result)


@router.websocket("/{neighbourhood_id}/ws")
async def alert_websocket(
    neighbourhood_id: UUID,
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    _ = token  # TODO: verify real Cognito token when auth is live

    claims = {
        "sub": "mock-websocket-user",
        "custom:role": "RESIDENT",
        "custom:neighbourhood_id": str(neighbourhood_id),
    }

    await websocket.accept()
    register_connection(str(neighbourhood_id), websocket)

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
