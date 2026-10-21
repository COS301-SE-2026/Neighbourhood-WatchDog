import pytest
from pydantic import ValidationError

from app.core.config import Config

REQUIRED = {
    "database_url": "postgresql+asyncpg://user:pass@localhost:5432/db",
    "redis_url": "redis://localhost:6379/0",
    "secret_key": "test-secret",
    "aws_region": "af-south-1",
    "cognito_region": "af-south-1",
    "cognito_user_pool_id": "af-south-1_test",
    "cognito_client_id": "test-client",
    "rtsp_encryption_key": "test-key",
}

SAFE = {
    "testing": False,
    "debug": False,
    "refresh_cookie_secure": True,
}
