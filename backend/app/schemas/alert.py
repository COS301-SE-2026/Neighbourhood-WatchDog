from enum import Enum
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel


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
    detection_event_id: UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AlertRes(BaseModel):
	id: UUID
	camera_id: UUID
	detection_event_id: UUID
	status: str
	resolved_by: UUID | None = None
	resolved_at: datetime | None = None
	created_at: datetime
	detection_type: str | None = None
	confidence_score: float | None = None
	thumbnail_url: str | None = None

	model_config = {"from_attributes": True}

class AcknowledgeAlertRes(BaseModel):
	status: int
	message: str | None = None
	data: AlertRes | None = None

class ListAlertsRes(BaseModel):
	status: int
	message: str | None = None
	data: list[AlertRes] | None = None

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
