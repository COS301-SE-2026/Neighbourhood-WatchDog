from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID


class UserRole(str, Enum):
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    RESIDENT = "RESIDENT"
    NEIGH_ADMIN = "NEIGH_ADMIN"
    PROP_ADMIN = "PROP_ADMIN"
    USER = "USER"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, unique=True)
    cognito_sub = Column(String)
    role = Column(SQLEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=func.now())


