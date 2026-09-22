

from uuid import UUID

from app.core.database import DbSession
from app.schemas.alert import IncidentDensityQuery


async def get_incident_density_handler(
    neighbourhood_id: UUID,
    filters: IncidentDensityQuery,
    db: DbSession,
    claims: dict,
):
    pass