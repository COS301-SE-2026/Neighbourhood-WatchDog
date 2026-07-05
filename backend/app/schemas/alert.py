from datetime import datetime
from uuid import UUID
from typing import Optional
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
      

