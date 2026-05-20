from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

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
