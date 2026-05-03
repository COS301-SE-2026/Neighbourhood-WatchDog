from fastapi import FastAPI
from app.core.logging import configure_logging
from app.core.config import config
from app.auth.middleware import AuthMiddleware
from app.api.controllers.auth import router as auth_router
from slowapi.middleware import SlowAPIMiddleware
from app.auth.rate_limiter import limiter

configure_logging()

app = FastAPI(title=config.app_name)
app.add_middleware(AuthMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter
app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}