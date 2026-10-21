from typing import Literal

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings

load_dotenv()

DEPLOYED_ENVS = {"staging", "production"}

class Config(BaseSettings):
    app_name: str = "NeighbourhoodWatchDog"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    database_url: str
    redis_url: str
    secret_key: str 

    aws_region: str
    cognito_region: str 
    cognito_user_pool_id: str 
    cognito_client_id: str

    frontend_url: str = "http://localhost:3000"

    osrm_base_url: str = "https://router.project-osrm.org"
    osrm_timeout_seconds: float = 5.0
    
    testing: bool = False
    rtsp_encryption_key: str

    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    refresh_cookie_max_age: int = 60 * 60 * 24 * 30

    firebase_credentials_json: str = ""

    @model_validator(mode="after")
    def fail_closed_in_deployed_envs(self) -> "Config":
        if self.app_env not in DEPLOYED_ENVS:
            return self
        if self.testing:
            raise ValueError(f"TESTING must be false when APP_ENV={self.app_env}")
        if self.debug:
            raise ValueError(f"DEBUG must be false when APP_ENV={self.app_env}")
        if not self.refresh_cookie_secure:
            raise ValueError(f"REFRESH_COOKIE_SECURE must be true when APP_ENV={self.app_env}")
        
        return self

config = Config()
