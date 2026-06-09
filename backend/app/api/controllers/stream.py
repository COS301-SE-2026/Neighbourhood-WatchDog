import asyncio
import json
from fastapi import APIRouter, WebSocket
from typing import Optional

router = APIRouter(prefix="/api/stream", tags=["stream"])

# Camera annotation connections: {camera_id: set[WebSocket]}
_annotation_connections: dict[str, set[WebSocket]] = {}

def _get_camera_bucket(camera_id: str) -> set[WebSocket]:
    if camera_id not in _annotation_connections:
        _annotation_connections[camera_id] = set()
    return _annotation_connections[camera_id]

def register_camera_connection(camera_id: str, websocket: WebSocket) -> None:
    _get_camera_bucket(camera_id).add(websocket)

def remove_camera_connection(camera_id: str, websocket: WebSocket) -> None:
    _get_camera_bucket(camera_id).discard(websocket)

async def broadcast_annotation(camera_id: str, annotation_data: dict) -> None:
    """Broadcast annotation data (bounding boxes, confidence, etc) to all connected clients"""
    connections = _get_camera_bucket(camera_id)
    dead: set[WebSocket] = set()
    
    payload = json.dumps(annotation_data)
    for ws in connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    
    for ws in dead:
        connections.discard(ws)

@router.post("/cameras/{camera_id}/annotations")
async def receive_annotation(camera_id: str, data: dict):
    """Receive annotation data from detector and broadcast to connected clients"""
    await broadcast_annotation(camera_id, {
        "camera_id": camera_id,
        "event": "annotation",
        **data  # Contains: tracks (list of {track_id, confidence, bbox}), timestamp
    })
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
