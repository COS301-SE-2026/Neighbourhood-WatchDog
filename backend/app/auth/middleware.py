from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/auth"): #If prefix is "/auth" we do not need authorization header
            return await call_next(request)

        public_routes = ["/health", "/docs", "/openapi.json", "/stream", "/alerts"]

        if request.url.path not in public_routes:
            if not request.headers.get("Authorization"):
                return JSONResponse({"detail": "No Authorization header"}, status_code=401)

        return await call_next(request)
