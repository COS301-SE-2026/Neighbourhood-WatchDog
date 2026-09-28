import json
import asyncio
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}

    def register(self, key: str, ws: WebSocket) -> None:
        if key not in self._connections:
            self._connections[key] = set()
        self._connections[key].add(ws)

    def remove(self, key: str, ws: WebSocket) -> None:
        connections = self._connections.get(key)
        if not connections:
            return
        connections.discard(ws)
        if not connections:
            self._connections.pop(key, None)

    async def broadcast(
        self,
        keys: list[str],
        message: dict,
    ) -> None:
        payload = json.dumps(message)
        for key in keys:
            connections = self._connections.get(key, set())
            
            if not connections:
                continue

            results = await asyncio.gather(
                *(ws.send_text(payload) for ws in connections),
                return_exceptions=True,
            )

            dead = {
                ws for ws, result in zip(connections, results)
                if isinstance(result, Exception)
            }
            for ws in dead:
                connections.discard(ws)

alert_connection_manager = ConnectionManager()