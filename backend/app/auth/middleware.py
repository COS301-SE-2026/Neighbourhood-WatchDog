from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # BaseHTTPMiddleware cannot handle WebSocket upgrades — pass them straight through.
        # Without this, the middleware kills the WS handshake and clients get code 1006.
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        PUBLIC_EXACT = {"/health", "/docs", "/openapi.json", "/redoc"}
        PUBLIC_PREFIXES = ["/stream", "/alerts", "/api/stream", "/auth"]


        is_public = (
            request.url.path in PUBLIC_EXACT or
            any(request.url.path.startswith(p) for p in PUBLIC_PREFIXES)
        )

        if not is_public:
            if not request.headers.get("Authorization"):
                return JSONResponse({"detail": "No Authorization header"}, status_code=401)

        return await call_next(request)
