

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}

    def register(self, key: str, ws: WebSocket) -> None:
        pass #TODO implement

    def remove(self, key: str, ws: WebSocket) -> None:
            pass #TODO implement

    async def broadcast(
        self,
        keys: list[str],
        message: dict,
    ) -> None:
        pass # TODO: implement