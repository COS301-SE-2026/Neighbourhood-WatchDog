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
        #Checking the origin
        public_routes = ["/health", "/docs", "/openapi.json", "/stream"]

        # Allow preflight requests without auth
        # TODO: remove this later
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response)
            return response

        frontend_origin = _normalize_origin(config.frontend_url)

        if not request.url.path in public_routes:
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
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
