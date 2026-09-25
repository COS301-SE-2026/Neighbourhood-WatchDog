import json
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
            dead: set[WebSocket] = set()
            
            for ws in connections:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.add(ws)

            for ws in dead:
                connections.discard(ws)