from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.core.config import config


def _normalize_origin(value: str | None) -> str | None:
    if not value:
        return None
    return value.rstrip("/")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # BaseHTTPMiddleware cannot handle WebSocket upgrades — pass them straight through.
        # Without this, the middleware kills the WS handshake and clients get code 1006.
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        PUBLIC_EXACT = {"/health", "/docs", "/openapi.json", "/redoc"}
        PUBLIC_PREFIXES = ["/stream", "/alerts", "/api/stream"]

        # Allow preflight requests without auth
        # TODO: remove this later
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response)
            return response

        frontend_origin = _normalize_origin(config.frontend_url)

        is_public = (
            request.url.path in PUBLIC_EXACT or
            any(request.url.path.startswith(p) for p in PUBLIC_PREFIXES)
        )

        if not is_public:
            if not request.headers.get("Authorization"):
                response = JSONResponse({"detail": "No Authorization header"}, status_code=401)
                self._add_cors_headers(response)
                return response

            origin = request.headers.get("Origin")
            if origin and _normalize_origin(origin) != frontend_origin:
                response = JSONResponse({"detail": "Origin not allowed"}, status_code=403)
                self._add_cors_headers(response)
                return response

        response = await call_next(request)
        self._add_cors_headers(response)
        return response

    def _add_cors_headers(self, response: Response):
        response.headers["Access-Control-Allow-Origin"] = _normalize_origin(config.frontend_url) or config.frontend_url
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, "
            "X-Mock-Role, X-Mock-Sub, X-Mock-Neighbourhood-Id, "
            "X-Mock-Email, X-Mock-First-Name, X-Mock-Last-Name"
        )
