from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import delete, func, select
from zoneinfo import ZoneInfo
from app.core.database import DbSession
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.incident_density import DailyIncidentDensity
from app.models.property import Property
from app.services.incident_density_grid import HISTORICAL_INCIDENT_STATUSES, incident_grid_expressions, CELL_SIZE_METRES


LOCAL_TIMEZONE = ZoneInfo("Africa/Johannesburg")

def _utc_day_bounds(target_date: date) -> tuple[datetime, datetime]:
    local_start = datetime.combine(
        target_date,
        time.min,
        tzinfo=LOCAL_TIMEZONE
    )
    local_end = local_start + timedelta(days=1)

    return (
        local_start.astimezone(timezone.utc),
        local_end.astimezone(timezone.utc)
    )

async def rebuild_incident_density_day(
    target_date: date,
    db: DbSession
) -> int:
    start_at, end_at = _utc_day_bounds(target_date)

    (
        grid_x,
        grid_y,
        latitude,
        longitude
    ) = incident_grid_expressions()

    statement = (
        select(
            Property.neighbourhood_id.label(
                "neighbourhood_id"
            ),
            grid_x.label("grid_x"),
            grid_y.label("grid_y"),
            latitude.label("latitude"),
            longitude.label("longitude"),
            func.count(Alert.id).label(
                "incident_count"
            )
        )
        .select_from(Alert)
        .join(Camera, Alert.camera_id == Camera.id)
        .join(Property, Camera.property_id == Property.id)
        .where(
            Property.neighbourhood_id.is_not(None),
            Property.latitude.is_not(None),
            Property.longitude.is_not(None),
            Alert.status.in_(HISTORICAL_INCIDENT_STATUSES),
            Alert.frame_timestamp >= start_at,
            Alert.frame_timestamp < end_at
        )
        .group_by(
            Property.neighbourhood_id,
            grid_x,
            grid_y,
            latitude,
            longitude
        )
    )

    result = await db.execute(statement)
    rows = result.mappings().all()

    # Rebuilding the date is idempotent.
    await db.execute(
        delete(DailyIncidentDensity).where(
            DailyIncidentDensity.incident_date == target_date
        )
    )

    db.add_all(
        [
            DailyIncidentDensity(
                neighbourhood_id=(
                    row["neighbourhood_id"]
                ),
                incident_date=target_date,
                cell_size_metres=(CELL_SIZE_METRES),
                grid_x=int(row["grid_x"]),
                grid_y=int(row["grid_y"]),
                latitude=float(
                    row["latitude"]
                ),
                longitude=float(
                    row["longitude"]
                ),
                incident_count=int(
                    row["incident_count"]
                ),
            )
            for row in rows
        ]
    )

    await db.commit()

    return len(rows)
