from pydantic import BaseModel

class LinkPropertyToken(BaseModel):
    token: str
    expires_at: int

class LinkPropertyTokenRes(BaseModel):
    status: int
    message: str | None = None
    data: LinkPropertyToken | None = None