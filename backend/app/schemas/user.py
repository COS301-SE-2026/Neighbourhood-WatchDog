from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from app.models.user import UserRole

class GetUserResSchema(BaseModel):
    id: UUID
    email: str
    cognito_sub: str
    role: UserRole
    created_at: datetime