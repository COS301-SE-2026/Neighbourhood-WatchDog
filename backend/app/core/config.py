from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Config(BaseSettings):
    app_name: str = "NeighbourhoodWatchDog"
    debug: bool = False
    database_url: str
    redis_url: str 
    secret_key: str 

    aws_region: str
    cognito_region: str 
    cognito_user_pool_id: str 
    cognito_client_id: str

    frontend_url: str

config = Config()