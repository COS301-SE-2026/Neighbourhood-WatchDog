from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.core.config import config

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

        if not any(request.url.path.startswith(route) for route in public_routes):
            if not request.headers.get("Authorization"):
                response = JSONResponse({"detail": "No Authorization header"}, status_code=401)
                self._add_cors_headers(response)
                return response

            origin = request.headers.get("Origin")
            if origin and origin != config.frontend_url:
                response = JSONResponse({"detail": "Origin not allowed"}, status_code=403)
                self._add_cors_headers(response)
                return response

        response = await call_next(request)
        self._add_cors_headers(response)
        return response

    def _add_cors_headers(self, response: Response):
        response.headers["Access-Control-Allow-Origin"] = config.frontend_url
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
