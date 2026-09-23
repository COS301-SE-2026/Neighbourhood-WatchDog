from datetime import date, datetime, time, timedelta, timezone


LOCAL_TIMEZONE = "Africa/Johannesburg"

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

