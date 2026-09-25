from sqlalchemy import Column, Float, ForeignKey, TIMESTAMP, UniqueConstraint, text
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
    )

    camera = relationship("Camera", back_populates="coverage")

    __table_args__ = (
        UniqueConstraint("camera_id", name="uq_camera_coverage_camera_id"),
    )