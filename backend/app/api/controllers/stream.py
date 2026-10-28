import asyncio
import json
from typing import Annotated
from fastapi import APIRouter, Depends, WebSocket, HTTPException
from sqlalchemy import select
from uuid import UUID
from fastapi import Query, status

from app.auth.jwt import verify_jwt
from app.auth.authorization import user_can_view_camera
from app.core.database import DbSession
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.models.camera import Camera
from app.api.controllers.internal_cameras import get_authenticated_edge_agent
from app.websocket.manager import ConnectionManager

router = APIRouter(prefix="/api/stream", tags=["stream"])

_manager = ConnectionManager()

def register_camera_connection(camera_id: str, websocket: WebSocket) -> None:
    _manager.register(camera_id, websocket)

def remove_camera_connection(camera_id: str, websocket: WebSocket) -> None:
    _manager.remove(camera_id, websocket)

async def broadcast_annotation(camera_id: str, annotation_data: dict) -> None: #TODO: make private, only accessible by internal services
    """Broadcast annotation data (bounding boxes, confidence, etc) to all connected clients"""
    await _manager.broadcast([camera_id], annotation_data)


@router.post("/cameras/{camera_id}/annotations")
async def receive_annotation(
    camera_id: UUID,
    data: dict,
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
) -> dict:
    owned_camera = await db.scalar(
        select(Camera.id).where(Camera.id == camera_id, Camera.property_id == credential.property_id)
    )

    if owned_camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found for this agent.")

    await broadcast_annotation(
        str(camera_id),
        {
            **data,
            "camera_id": str(camera_id),
            "event": "annotation",
        },
    )

    return {"status": "broadcasted"}


@router.websocket("/cameras/{camera_id}/annotations/ws")
async def camera_annotation_websocket(
    camera_id: UUID, 
    websocket: WebSocket,
    db: DbSession,
    token: Annotated[str, Query()],
):
    """WebSocket endpoint for receiving annotation updates for a specific camera"""
    try:
        claims = verify_jwt(token)
        if not await user_can_view_camera(db, claims, camera_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    connection_key = str(camera_id)
    await websocket.accept()
    register_camera_connection(connection_key, websocket)

    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"event": "ping"}))
    except Exception:
        pass
    finally:
        remove_camera_connection(connection_key, websocket)