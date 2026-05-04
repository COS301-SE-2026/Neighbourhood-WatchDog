from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base

class UserRole(str, Enum):
    SYSTEM_ADMIN = "system_admin"
    RESIDENT = "resident"
    NEIGH_ADMIN = "neigh_admin"
    PROP_ADMIN = "prop_admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    cognito_sub = Column(String)
    role = Column(SQLEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=func.now())

