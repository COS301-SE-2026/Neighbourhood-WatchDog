from fastapi import HTTPException

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth.jwt import get_authenticated_claims

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # BaseHTTPMiddleware cannot handle WebSocket upgrades — pass them straight through.
        # Without this, the middleware kills the WS handshake and clients get code 1006.
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        PUBLIC_EXACT = {"/health", "/docs", "/openapi.json", "/redoc"}
        PUBLIC_PREFIXES = ["/stream", "/alerts", "/api/stream", "/auth", "/internal"]


        is_public = (
            request.url.path in PUBLIC_EXACT or
            any(request.url.path.startswith(p) for p in PUBLIC_PREFIXES)
        )

        if is_public:
            return await call_next(request)

        try:
            get_authenticated_claims(request) #verify JWT and set claims(data from JWT)
        except HTTPException as e:
            return JSONResponse(
                {"detail": e.detail},
                status_code=e.status_code,
            )

        return await call_next(request)