from app import models  # noqa: F401  (imported for side effects: model registration)
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from app.core.app_logging import configure_logging
from app.core.config import config
from app.auth.middleware import AuthMiddleware
from app.api.controllers.auth import router as auth_router
from app.api.controllers.neighbourhood_join import router as neighbourhood_join_router
from app.api.controllers.alert import router as alert_router
from app.api.controllers.audit import router as audit_router
from app.api.controllers.camera import router as camera_router
from app.api.controllers.camera_settings import router as camera_settings_router
from app.api.controllers.clips import router as clips_router
from app.api.controllers.detection import router as detection_router
from app.api.controllers.internal import router as internal_router
from app.api.controllers.internal_cameras import router as internal_cameras_router
from app.api.controllers.internal_failover import router as internal_failover_router
from app.api.controllers.neighbourhood import router as neighbourhood_router
from app.api.controllers.notification import router as notification_router
from app.api.controllers.pairing_token import router as pairing_token_router
from app.api.controllers.property import router as property_router
from app.api.controllers.risk_score_history import router as risk_score_history_router
from app.api.controllers.risk_threshold_config import router as risk_threshold_router
from app.api.controllers.stream import router as stream_router
from app.api.controllers.users import router as users_router
from app.auth.rate_limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

configure_logging(config.debug and "DEBUG" or "INFO")


app = FastAPI(
    title=config.app_name,
    openapi_url="/openapi.json", # if config.debug else None, TODO consider uncommenting
    docs_url="/docs", # if config.debug else None,
    redoc_url="/redoc", # if config.debug else None,
)

if config.testing: #Disable the limiter during testing, preventing exception 429
    limiter.enabled = False

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(AuthMiddleware) #Which routes are public and private
app.add_middleware(SlowAPIMiddleware) #Rate limiting 

app.add_middleware( #CORS (allow requests from frontend)
    CORSMiddleware,
    allow_origins=[config.frontend_url.rstrip("/"), "http://localhost:3000", "https://neighbourhood-watch-dog-intrepidcapstone-4790-teamintrepid.vercel.app", "https://neighbourhood-watch-dog.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth_router)
app.include_router(neighbourhood_join_router)
app.include_router(alert_router)
app.include_router(detection_router)
app.include_router(internal_cameras_router)
app.include_router(property_router)
app.include_router(neighbourhood_router)
app.include_router(camera_router)
app.include_router(users_router)
app.include_router(stream_router)
app.include_router(notification_router)
app.include_router(audit_router)
app.include_router(camera_settings_router)
app.include_router(clips_router)
app.include_router(internal_router)
app.include_router(internal_failover_router)
app.include_router(risk_score_history_router)
app.include_router(pairing_token_router)
app.include_router(risk_threshold_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}


def custom_openapi():
    """This is for the API Service Contract to make sure it returns the full schema, not just a reference"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    schemas = openapi_schema.get("components", {}).get("schemas", {})

    openapi_schema["paths"] = _resolve_refs(openapi_schema["paths"], schemas)

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

def _resolve_refs(node, schemas, seen=frozenset()):
    """Helper function for custom_openapi which resolves $ref references inline"""
    if isinstance(node, dict):
        if "$ref" in node:
            key = node["$ref"].rsplit("/", 1)[-1]
            if key in seen:
                return node
            target = schemas.get(key)
            if target is None:
                return node

            resolved = _resolve_refs(target, schemas, seen | {key})
            extras = {k: v for k, v in node.items() if k != "$ref"}
            if extras:
                return {**resolved, **_resolve_refs(extras, schemas, seen)}
            return resolved
        return {k: _resolve_refs(v, schemas, seen) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, schemas, seen) for item in node]
    return node