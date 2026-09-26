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


class DangerZoneCell(Base):
    __tablename__ = "danger_zone_cell"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neighbourhood_id = Column(UUID(as_uuid=True),ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=False)
    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    cell_size_metres = Column(SmallInteger, nullable=False, server_default="100")
    grid_x = Column(BigInteger, nullable=False)
    grid_y = Column(BigInteger,nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float,nullable=False)
    incident_count = Column(Integer, nullable=False)
    incident_score = Column(Float, nullable=False)
    coverage_ratio = Column(Float, nullable=False)
    coverage_sparsity = Column(Float, nullable=False)
    danger_score = Column(Float, nullable=False)
    calculated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint(
            "neighbourhood_id",
            "window_end",
            "grid_x",
            "grid_y",
            name="uq_danger_zone_cell_snapshot"
        ),
        CheckConstraint(
            "window_start <= window_end",
            name="ck_danger_zone_valid_window"
        ),
        CheckConstraint(
            "incident_count >= 0",
            name="ck_danger_zone_incident_count"
        ),
        CheckConstraint(
            "incident_score BETWEEN 0 AND 1",
            name="ck_danger_zone_incident_score"
        ),
        CheckConstraint(
            "coverage_ratio BETWEEN 0 AND 1",
            name="ck_danger_zone_coverage_ratio"
        ),
        CheckConstraint(
            "coverage_sparsity BETWEEN 0 AND 1",
            name="ck_danger_zone_coverage_sparsity"
        ),
        CheckConstraint(
            "danger_score BETWEEN 0 AND 1",
            name="ck_danger_zone_danger_score"
        ),
        Index(
            "ix_danger_zone_neighbourhood_window",
            "neighbourhood_id",
            "window_end"
        ),
    )
