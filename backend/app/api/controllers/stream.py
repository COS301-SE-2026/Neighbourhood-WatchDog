import asyncio
import json
from typing import Annotated
from fastapi import APIRouter, Depends,WebSocket

from app.models.edge_agent_credentials import EdgeAgentCredential
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


@router.post("/cameras/{camera_id}/annotations") #TODO: make private, only accessible by internal services
async def receive_annotation(
    camera_id: str,
    data: dict,
    x_internal_token: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
) -> dict:
    

    await broadcast_annotation(
        camera_id,
        {
            "camera_id": camera_id,
            "event": "annotation",
            **data,
        },
    )

    return {"status": "broadcasted"}


@router.websocket("/cameras/{camera_id}/annotations/ws")
async def camera_annotation_websocket(camera_id: str, websocket: WebSocket):
    """WebSocket endpoint for receiving annotation updates for a specific camera"""
    await websocket.accept()
    register_camera_connection(camera_id, websocket)

    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"event": "ping"}))
    except Exception:
        pass
    finally:
        remove_camera_connection(camera_id, websocket)