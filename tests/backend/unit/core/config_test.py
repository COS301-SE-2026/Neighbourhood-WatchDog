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

def make_config(**overrides) -> Config:
    return Config(**{**REQUIRED, **SAFE, **overrides})

@pytest.mark.parametrize("app_env", ["staging", "production"])
def test_deployed_env_accepts_safe_settings(app_env):
    config = make_config(app_env=app_env)

    assert config.app_env == app_env

@pytest.mark.parametrize("app_env", ["staging", "production"])
@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"testing": True}, "TESTING must be false"),
        ({"debug": True}, "DEBUG must be false"),
        ({"refresh_cookie_secure": False}, "REFRESH_COOKIE_SECURE must be true"),
    ],
)
def test_deployed_env_rejects_unsafe_settings(app_env, override, message):
    with pytest.raises(ValidationError, match=message):
        make_config(app_env=app_env, **override)


@pytest.mark.parametrize("app_env", ["development", "test"])
def test_local_env_allows_testing_and_debug(app_env):
    config = make_config(
        app_env=app_env,
        testing=True,
        debug=True,
        refresh_cookie_secure=False,
    )
    assert config.testing is True
    assert config.debug is True


def test_unknown_app_env_is_rejected():
    with pytest.raises(ValidationError):
        make_config(app_env="prod")


def test_app_env_defaults_to_development(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    config = make_config()
    assert config.app_env == "development"