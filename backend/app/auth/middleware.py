from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import config
from fastapi import HTTPException

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        #Checking the origin
        public_routes = ["/health", "/docs", "/openapi.json"]

        print("Frontend url" + config.frontend_url)

        # Allow preflight requests without auth
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = config.frontend_url
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response

        if not request.url.path in public_routes:
            if not request.headers.get("Authorization"):
                raise HTTPException(status_code=401, detail="No Authorization header")

            if request.headers.get("Origin") != config.frontend_url:
                raise HTTPException(status_code=403, detail="Origin not allowed")

        response = await call_next(request)

        response.headers["Access-Control-Allow-Origin"] = config.frontend_url
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response
