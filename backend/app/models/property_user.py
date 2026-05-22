from sqlalchemy import Column, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class PropertyUser(Base):
    __tablename__ = "property_user"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id"), primary_key=True)
    is_admin = Column(Boolean, nullable=False, default=False)

    user = relationship("User", foreign_keys=[user_id])
    proper = relationship("Property", foreign_keys=[property_id])