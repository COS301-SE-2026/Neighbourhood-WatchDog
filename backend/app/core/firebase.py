import json
import firebase_admin
from firebase_admin import credentials
from app.core.config import config

def init_firebase() -> None:
    if not config.firebase_credentials_json or firebase_admin._apps:
        return

    cred = credentials.Certificate(json.loads(config.firebase_credentials_json))
    firebase_admin.initialize_app(cred)

