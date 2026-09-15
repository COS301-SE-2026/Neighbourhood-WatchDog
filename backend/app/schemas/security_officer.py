from uuid import UUID
from pydantic import BaseModel

from app.models.security_officer import AvailabilityStatus
from app.schemas.property import NonEmptyString

class UpdateSecurityAvailability(BaseModel):
    neighbourhood_id = UUID
    new_availability = AvailabilityStatus

class UpdateSecurityAvailabilityResponse(BaseModel):
    status: int
    message: str | None = None