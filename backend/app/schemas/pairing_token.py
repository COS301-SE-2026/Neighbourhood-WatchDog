from pydantic import BaseModel
from datetime import datetime

class LinkPropertyToken(BaseModel):
    token: str
    expires_at: datetime

class LinkPropertyTokenRes(BaseModel):
    status: int
    message: str | None = None
    data: LinkPropertyToken | None = None