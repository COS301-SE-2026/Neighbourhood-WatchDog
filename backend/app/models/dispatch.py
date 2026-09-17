import uuid
from enum import Enum
from sqlalchemy import CheckConstraint, Column, Index, ForeignKey, text, TIMESTAMP, Enum as SAEnum, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class DispatchStatus(str, Enum):
    SELECTED = "SELECTED" #primary officer chosen
    QUEUED = "QUEUED" #for busy officers
    NOTIFIED = "NOTIFIED" #officer notified waiting for response
    ACCEPTED = "ACCEPTED" #accepts dispatch request
    DECLINED = "DECLINED" #declines dispatch request
    TIMED_OUT = "TIMED_OUT" #officer did not respond on time
    NO_CANDIDATE = "NO_CANDIDATE" #no eligible officer exists for dispatch request

class Dispatch(Base):
    __tablename__ = "dispatch"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alert.id", ondelete="CASCADE"), nullable=False)
    neighbourhood_id = Column(UUID(as_uuid=True), ForeignKey("neighbourhood.id", ondelete="CASCADE"), nullable=False)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("security_officer.id", ondelete="CASCADE"), nullable=True)
    rank = Column(Integer, nullable=False) 
    score = Column(Float, nullable=True) #lower score is better
    distance = Column(Float, nullable=True) #distance from alert in metres
    eta = Column(Float, nullable=True) #eta to alert in seconds
    workload = Column(Integer, nullable=True)
    status = Column(SAEnum(DispatchStatus, name="dispatch_status"), nullable=False, default=DispatchStatus.SELECTED)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    responded_at = Column(TIMESTAMP(timezone=True), nullable=True)

    #relationships
    alert = relationship("Alert", back_populates="dispatch")
    neighbourhood = relationship("Neighbourhood", back_populates="dispatches")
    officer = relationship("SecurityOfficer", back_populates="dispatch", foreign_keys=[officer_id])

    #indexes
    __table_args__ = (
        Index("ix_dispatch_alert_rank", "alert_id", "rank"),
        Index("ix_dispatch_officer", "officer_id"),
        Index("ix_dispatch_neighbourhood", "neighbourhood_id"),
        Index("ix_dispatch_neighbourhood_status", "neighbourhood_id", "status"),
        Index("uq_dispatch_alert_officer", "alert_id", "officer_id", unique=True, postgresql_where=text("officer_id IS NOT NULL")),

        CheckConstraint(
            "(status = 'NO_CANDIDATE' AND officer_id IS NULL) "
            "OR (status != 'NO_CANDIDATE' AND officer_id IS NOT NULL)",
            name="ck_dispatch_officer_matches_status",
        ),
        CheckConstraint("rank > 0", name="ck_dispatch_rank_positive"),
    )