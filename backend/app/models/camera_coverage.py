from sqlalchemy import (
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    TIMESTAMP,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CameraCoverage(Base):
    __tablename__ = "camera_coverage"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    camera_id = Column(
        UUID(as_uuid=True),
        ForeignKey("camera.id", ondelete="CASCADE"),
        nullable=False,
    )
    origin_latitude = Column(Float, nullable=False)
    origin_longitude = Column(Float, nullable=False)
    coverage_bearing_degrees = Column(Float, nullable=False)
    coverage_angle_degrees = Column(Float, nullable=False)
    coverage_range_metres = Column(Float, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )

    camera = relationship("Camera", back_populates="coverage")

    __table_args__ = (
        UniqueConstraint(
            "camera_id",
            name="uq_camera_coverage_camera_id",
        ),
        CheckConstraint(
            "origin_latitude BETWEEN -90 AND 90",
            name="ck_camera_coverage_latitude",
        ),
        CheckConstraint(
            "origin_longitude BETWEEN -180 AND 180",
            name="ck_camera_coverage_longitude",
        ),
        CheckConstraint(
            "coverage_bearing_degrees >= 0 "
            "AND coverage_bearing_degrees < 360",
            name="ck_camera_coverage_bearing",
        ),
        CheckConstraint(
            "coverage_angle_degrees BETWEEN 1 AND 180",
            name="ck_camera_coverage_angle",
        ),
        CheckConstraint(
            "coverage_range_metres BETWEEN 1 AND 200",
            name="ck_camera_coverage_range",
        ),
    )