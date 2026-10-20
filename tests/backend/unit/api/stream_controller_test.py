import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import WebSocketDisconnect, status

from app.api.controllers import stream

CAMERA_ID = uuid4()
CLAIMS = {"sub": "cognito-user-123"}

def make_websocket(*receive_effects):
   websocket = MagicMock()
   websocket.accept = AsyncMock()
   websocket.close = AsyncMock()
   websocket.send_text = AsyncMock()
   websocket.receive_text = AsyncMock(
       side_effect=list(receive_effects) or [WebSocketDisconnect()]
   )
   return websocket

@pytest.mark.asyncio
async def test_annotation_websocket_rejects_invalid_token():
   websocket = make_websocket()

   with (
       patch.object(stream, "verify_jwt", side_effect=Exception("bad token")),
       patch.object(stream, "user_can_view_camera", new=AsyncMock()) as can_view,
       patch.object(stream, "register_camera_connection") as register,
   ):
       await stream.camera_annotation_websocket(
           CAMERA_ID, websocket, MagicMock(), "bad-token"
       )

   websocket.close.assert_awaited_once_with(code=status.WS_1008_POLICY_VIOLATION)
   websocket.accept.assert_not_awaited()
   can_view.assert_not_awaited()
   register.assert_not_called()

@pytest.mark.asyncio
async def test_annotation_websocket_rejects_user_without_camera_access():
   websocket = make_websocket()
   db = MagicMock()

   with (
       patch.object(stream, "verify_jwt", return_value=CLAIMS),
       patch.object(
           stream, "user_can_view_camera", new=AsyncMock(return_value=False)
       ) as can_view,
       patch.object(stream, "register_camera_connection") as register,
   ):
       await stream.camera_annotation_websocket(CAMERA_ID, websocket, db, "token")

   can_view.assert_awaited_once_with(db, CLAIMS, CAMERA_ID)
   websocket.close.assert_awaited_once_with(code=status.WS_1008_POLICY_VIOLATION)
   websocket.accept.assert_not_awaited()
   register.assert_not_called()

@pytest.mark.asyncio
async def test_annotation_websocket_rejects_when_access_check_raises():
   websocket = make_websocket()

   with (
       patch.object(stream, "verify_jwt", return_value=CLAIMS),
       patch.object(
           stream,
           "user_can_view_camera",
           new=AsyncMock(side_effect=RuntimeError("db down")),
       ),
       patch.object(stream, "register_camera_connection") as register,
   ):
       await stream.camera_annotation_websocket(
           CAMERA_ID, websocket, MagicMock(), "token"
       )

   websocket.close.assert_awaited_once_with(code=status.WS_1008_POLICY_VIOLATION)
   websocket.accept.assert_not_awaited()
   register.assert_not_called()

@pytest.mark.asyncio
async def test_annotation_websocket_accepts_and_registers_allowed_viewer():
   websocket = make_websocket(WebSocketDisconnect())

   with (
       patch.object(stream, "verify_jwt", return_value=CLAIMS),
       patch.object(
           stream, "user_can_view_camera", new=AsyncMock(return_value=True)
       ),
       patch.object(stream, "register_camera_connection") as register,
       patch.object(stream, "remove_camera_connection") as remove,
   ):
       await stream.camera_annotation_websocket(
           CAMERA_ID, websocket, MagicMock(), "token"
       )

   websocket.accept.assert_awaited_once()
   websocket.close.assert_not_awaited()
   # The connection key must be the string form, matching what the edge
   # agent broadcasts with, and the same key must be used to remove it.
   register.assert_called_once_with(str(CAMERA_ID), websocket)
   remove.assert_called_once_with(str(CAMERA_ID), websocket)

@pytest.mark.asyncio
async def test_annotation_websocket_sends_ping_when_idle():
   websocket = make_websocket(asyncio.TimeoutError(), WebSocketDisconnect())

   with (
       patch.object(stream, "verify_jwt", return_value=CLAIMS),
       patch.object(
           stream, "user_can_view_camera", new=AsyncMock(return_value=True)
       ),
       patch.object(stream, "register_camera_connection"),
       patch.object(stream, "remove_camera_connection") as remove,
   ):
       await stream.camera_annotation_websocket(
           CAMERA_ID, websocket, MagicMock(), "token"
       )

   websocket.send_text.assert_awaited_once_with('{"event": "ping"}')
   remove.assert_called_once_with(str(CAMERA_ID), websocket)

@pytest.mark.asyncio
async def test_receive_annotation_broadcasts_to_camera_viewers():
   camera_id = str(uuid4())

   with patch.object(stream, "broadcast_annotation", new=AsyncMock()) as broadcast:
       result = await stream.receive_annotation(
           camera_id,
           {"tracks": [], "timestamp": "2026-10-20T10:00:00Z"},
           MagicMock(),
       )

   assert result == {"status": "broadcasted"}
   broadcast.assert_awaited_once_with(
       camera_id,
       {
           "camera_id": camera_id,
           "event": "annotation",
           "tracks": [],
           "timestamp": "2026-10-20T10:00:00Z",
       },
   )


