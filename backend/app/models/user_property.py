from app.core.database import Base
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID


class UserProperty(Base):
    __tablename__ = "user_property"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("property.id", ondelete="CASCADE"), primary_key=True, nullable=False)