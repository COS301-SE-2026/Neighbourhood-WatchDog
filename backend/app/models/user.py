from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4


class UserRole(str, Enum):
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    RESIDENT = "RESIDENT"
    NEIGHBOURHOOD_ADMIN = "NEIGHBOURHOOD_ADMIN"
    SECURITY_OFFICER = "SECURITY_OFFICER"
    PROPERTY_ADMIN = "PROPERTY_ADMIN"
    USER = "USER"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    cognito_sub = Column(String, unique=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.RESIDENT)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    neighbourhood = relationship("Neighbourhood", back_populates="users")
    join_requests = relationship("NeighbourhoodJoinRequest", back_populates="user")
    resolved_alerts = relationship("Alert", back_populates="resolver")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


