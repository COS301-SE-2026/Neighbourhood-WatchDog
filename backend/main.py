from fastapi import FastAPI
from app.core.logging import configure_logging
from app.core.config import config
from app.auth.middleware import AuthMiddleware
from app.api.controllers.auth import router as auth_router
from app.api.controllers.property import router as property_router
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
app.include_router(property_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}