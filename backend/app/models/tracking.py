import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from pgvector.sqlalchemy import Vector


APPEARANCE_EMBEDDING_DIMENSION = 1280
APPEARANCE_EMBEDDING_MODEL = "deep_sort_mobilenet_v2_bottleneck" ##using deepsorts fast-lightweight brain (MobileNetV2) to create visual fingerprints (bottleneck) to identify obj on stream
#using this cause CNN is too heavy on computational complexity

class TrackingSubject(Base):
    __tablename__ = "tracking_subject"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ## existing Alert acts as the incident / tracking-session root
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alert.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    reference_embedding = Column(Vector(APPEARANCE_EMBEDDING_DIMENSION),nullable=True)
    embedding_model = Column(String(128), nullable=True)

    alert = relationship("Alert", back_populates="tracking_subject")
    sightings = relationship("TrackingSighting", back_populates="tracking_subject", cascade="all, delete-orphan", order_by="TrackingSighting.sequence_no")


#represents one observation of the tracked sighting
class TrackingSighting(Base):
    __tablename__ = "tracking_sighting"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tracking_subject_id = Column(UUID(as_uuid=True), ForeignKey("tracking_subject.id", ondelete="CASCADE"), nullable=False)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("camera.id", ondelete="CASCADE"), nullable=False)

    #deepsort ids are local to one camera
    local_track_id = Column(Integer, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    sequence_no = Column(Integer, nullable=False)

    #  appearance match confidence, not threat confidence
    match_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    tracking_subject = relationship("TrackingSubject", back_populates="sightings")


    camera = relationship("Camera")

    __table_args__ = (

        UniqueConstraint("tracking_subject_id", "sequence_no", name="uq_tracking_sighting_subject_sequence"),
        CheckConstraint("sequence_no > 0", name="ck_tracking_sighting_sequence_positive"),
        CheckConstraint(
            "match_confidence IS NULL OR (match_confidence >= 0 AND match_confidence <= 1)",
            name="ck_tracking_sighting_confidence_range",
        ),
        Index("ix_tracking_sighting_subject_observed_at", "tracking_subject_id", "observed_at"), #subject and time
        Index("ix_tracking_sighting_camera_observed_at", "camera_id", "observed_at"), #camera and time


    )
