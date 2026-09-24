import uuid

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    TIMESTAMP,
    UniqueConstraint,
    text
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class DailyIncidentDensity(Base):
    __tablename__ = "daily_incident_density"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=False)
    incident_date = Column(Date, nullable=False)
    cell_size_metres = Column(SmallInteger, nullable=False, server_default="100")
    grid_x = Column(BigInteger, nullable=False)
    grid_y = Column(BigInteger, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    incident_count = Column(Integer, nullable=False)
    computed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint(
            "neighbourhood_id",
            "incident_date",
            "cell_size_metres",
            "grid_x",
            "grid_y",
            name="uq_daily_incident_density_cell"
        ),
        CheckConstraint(
            "incident_count > 0",
            name=(
                "ck_daily_incident_density_"
                "positive_count"
            ),
        ),
        Index(
            "ix_daily_incident_density_lookup",
            "neighbourhood_id",
            "incident_date"
        )
    )
