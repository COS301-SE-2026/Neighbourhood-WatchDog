from enum import Enum
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    camera_id: Optional[UUID] = None
    neighbourhood_id: Optional[UUID] = None
    detection_type: str = "HUMAN_PRESENCE"
    confidence: float
    timestamp: datetime
    thumbnail_url: Optional[str] = None


class AlertResponse(BaseModel):
    id: UUID
    camera_id: UUID
    status: str
    created_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)

class AlertRes(BaseModel):
    id: UUID
    camera_id: UUID
    frame_timestamp: datetime
    detection_type: str
    confidence_score: float
    thumbnail_url: str | None = None
    clip_s3_key: str | None = None
    clip_expires_at: datetime | None = None
    processed: bool
    status: str
    resolved_by: UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    property_address: str | None = None
    property_latitude: float | None = None
    property_longitude: float | None = None

    model_config = {"from_attributes": True}

class AcknowledgeAlertRes(BaseModel):
	status: int
	message: str | None = None
	data: AlertRes | None = None

class Pagination(BaseModel):
	total: int
	limit: int
	offset: int
	has_more: bool
class ListAlertsRes(BaseModel):
	status: int
	message: str | None = None
	data: list[AlertRes] | None = None
	pagination: Pagination | None = None

class AlertMetricItem(BaseModel):
	alert_id: UUID
	camera_id: UUID
	status: str
	response_seconds: float | None = None
	acknowledged_by: UUID | None = None
	created_at: datetime

	model_config = {"from_attributes": True}
      
class AlertMetricsRes(BaseModel):
	total_alerts: int
	acknowledged_count: int
	pending_count: int
	average_response_seconds: float | None = None
	items: list[AlertMetricItem]
	pagination: Pagination
      
class TimeIntervalsEnum(str, Enum):
	DAILY = "DAILY"
	MONTHLY = "MONTHLY"
	YEARLY = "YEARLY"

class TimePeriod(str, Enum):
	WEEK = "WEEK"
	MONTH = "MONTH"
	THREE_MONTHS = "THREE_MONTHS"
	SIX_MONTHS = "SIX_MONTHS"
	YEAR = "YEAR"
	TOTAL = "TOTAL"

class NumberInPeriod(BaseModel):
	period: List[datetime]
	count: List[int]

class AlertFrequencyMetricsRes(BaseModel):
	status: int
	message: str | None = None
	data: NumberInPeriod | None = None


class TrendGroupBy(str, Enum):
	DAY = "DAY"
	WEEK = "WEEK"
	MONTH = "MONTH"


class TrendDirection(str, Enum):
	UP = "UP"
	DOWN = "DOWN"
	STABLE = "STABLE"


class TrendBucket(BaseModel):
	period: datetime
	count: int


class TrendData(BaseModel):
	bucket: list[TrendBucket]
	total_count: int
	direnction: TrendDirection


class TrendResponse(BaseModel):
	status: int
	message: str
	data: TrendData | None = None

class BroadcastAlertReq(BaseModel):
    alert_id: UUID

class CreateInternalAlertRequest(BaseModel):
    """Represent an alert-creation request sent by an authenticated AI agent."""

    camera_id: str
    detection_type: str
    confidence_score: float
    local_track_id: int | None = None
    thumbnail_url: str | None = None
    frame_timestamp: str | None = None


	#represent 'fingerprints' of object
    appearance_embedding: list[float] | None = Field(
		default=None, 
		min_length=1280, 
		max_length=1280	
	)

	#specify the model ie, mobilenet_v2
    embedding_model: str | None = Field(
		default=None, 
		min_length=1, 
		max_length=128
	)


class UpdateAlertClipRequest(BaseModel):
    """Represent an AI agent request to attach a clip to an alert."""

    clip_s3_key: str
    clip_expires_at: str


class InternalAlertCreateRes(BaseModel):
    """Represent the identifier of an alert created by an AI agent."""

    alert_id: UUID


class AlertClipUpdateRes(BaseModel):
    """Represent an alert after its clip details have been updated."""

    alert_id: UUID
    clip_s3_key: str
    clip_expires_at: datetime


class ClipUploadAcceptedRes(BaseModel):
	"""Response when the clip has been accepted but not necessarily uploaded yet"""

	alert_id: UUID
	status: str

class CriticalAlertBase(BaseModel):
    id: UUID
    camera_id: UUID
    camera_name: str
    neighbourhood_id: UUID
    detection_type: str
    status: str
    created_at: datetime
    property_id: UUID
    property_address: str
    thumbnail_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

class CriticalAlertMapItem(CriticalAlertBase):
	latitude: float 
	longitude: float

class UnlocatedCriticalAlertItem(CriticalAlertBase):
	latitude: float | None = None
	longitude: float | None = None


class CriticalAlertMapData(BaseModel):
    alerts: list[CriticalAlertMapItem]
    last_updated: datetime


class CriticalAlertMapRes(BaseModel):
    status: int
    message: str | None = None
    data: CriticalAlertMapData

class UnlocatedCriticalAlertsData(BaseModel):
    alerts: list[UnlocatedCriticalAlertItem]
    last_updated: datetime

class UnlocatedCriticalAlertsRes(BaseModel):
    status: int
    message: str | None = None
    data: UnlocatedCriticalAlertsData