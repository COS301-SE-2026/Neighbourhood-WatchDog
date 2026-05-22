from fastapi import FastAPI
from app.core.logging import configure_logging
from app.core.config import config
from app.auth.middleware import AuthMiddleware
from app.api.controllers.auth import router as auth_router
from app.api.controllers.neighbourhood_join import router as neighbourhood_join_router
from app.api.controllers.alert import router as alert_router
from app.api.controllers.detection import router as detection_router
from app.api.controllers.property import router as property_router
from app.api.controllers.neighbourhood import router as neighbourhood_router
from app.api.controllers.camera import router as camera_router
from app.api.controllers.alert import router as alerts_router
from app.api.controllers.stream import router as stream_router
from slowapi.middleware import SlowAPIMiddleware
from app.auth.rate_limiter import limiter
from app.core.database import engine, Base
import app.models

configure_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=config.app_name,
    openapi_url="/openapi.json" if config.debug else None,
    docs_url="/docs" if config.debug else None,
    redoc_url="/redoc" if config.debug else None,
)
app.add_middleware(AuthMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter

app.include_router(auth_router)
app.include_router(neighbourhood_join_router)
app.include_router(alert_router)
app.include_router(detection_router)
app.include_router(property_router)
app.include_router(neighbourhood_router)
app.include_router(camera_router)
app.include_router(alerts_router)
app.include_router(stream_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}