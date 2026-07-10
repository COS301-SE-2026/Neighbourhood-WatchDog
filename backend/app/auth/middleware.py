from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth.jwt import verify_jwt

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

        if is_public:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not is_public:
            if not auth_header:#does it have JWT
                return JSONResponse({"detail": "No Authorization header"}, status_code=401)

        if not auth_header.startswith("Bearer "):#extract JWT
            return JSONResponse({"detail": "Invalid Authorization header"}, status_code=401)

        token = auth_header.split(" ", 1)[1] #get jwt

        try:
            claims = verify_jwt(token)
        except JWTError:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        request.state.claims = claims

        return await call_next(request)