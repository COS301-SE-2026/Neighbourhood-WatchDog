from datetime import datetime, date
from uuid import UUID
from app.services.camera_cache import _norm

def alerts_neighbourhood_cache_key(
    neighbourhood_id: str | UUID,
    status_filter: str | None = None,
    camera_id: UUID | None = None,
    detection_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 0,
    offset: int = 0,
) -> str:
    return (
        f"cache:alerts:neighbourhood:{_norm(neighbourhood_id)}"
        f":{status_filter or ''}:{camera_id or ''}:{detection_type or ''}"
        f":{start_date or ''}:{end_date or ''}:{limit}:{offset}"
    )


def incident_density_cache_key(
    neighbourhood_id: str | UUID,
    start_date: date,
    end_date: date,
    west: float,
    south: float,
    east: float,
    north: float,
) -> str:
    return (
        f"cache:incident_density:{_norm(neighbourhood_id)}"
        f":{start_date}:{end_date}:{west}:{south}:{east}:{north}"
    )