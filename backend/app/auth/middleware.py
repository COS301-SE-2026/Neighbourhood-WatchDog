import re
from fastapi import HTTPException

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth.jwt import get_authenticated_claims

PUBLIC_EXACT = frozenset({
    "/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico",
    "/auth/login", "/auth/signup", "/auth/confirm", "/auth/resend-code", 
    "/auth/verify-mfa", "/auth/refresh", "/auth/logout",
    "/internal/*", "/internal/mediamtx/auth", "/auth/ping"
})

PUBLIC_PATTERNS = [
    re.compile(r"/pairing-token/token/[^/]+"),
    # Edge-agent routes. Ech one authenticates itself with X-internal-token
    re.compile(r"/internal/.+"),
]

def is_public_path(path: str) -> bool:
    return path in PUBLIC_EXACT or any(p.fullmatch(path) for p in PUBLIC_PATTERNS)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # BaseHTTPMiddleware cannot handle WebSocket upgrades - pass them straight through.
        # Without this, the middleware kills the WS handshake and clients get code 1006.
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        if is_public_path(request.url.path):
            return await call_next(request)

        try:
            get_authenticated_claims(request) #verify JWT and set claims(data from JWT)
        except HTTPException as e:
            return JSONResponse(
                {"detail": e.detail},
                status_code=e.status_code,
            )

        return await call_next(request)

    