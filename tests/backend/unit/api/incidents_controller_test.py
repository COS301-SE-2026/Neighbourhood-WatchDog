from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.controllers.incidents import (
    get_incident,
    list_incidents,
)
from app.schemas.alert import (
    AlertRes,
    IncidentDetailRes,
    IncidentSummaryRes,
)


def make_alert_response(alert_id):
    now = datetime.now(timezone.utc)

    return AlertRes(
        id=alert_id,
        camera_id=uuid4(),
        incident_id=uuid4(),
        frame_timestamp=now,
        detection_type="WEAPON_DETECTED",
        confidence_score=0.95,
        thumbnail_url=None,
        clip_s3_key=None,
        clip_expires_at=None,
        tracking_subject_id=None,
        processed=True,
        status="OPEN",
        resolved_by=None,
        resolved_at=None,
        created_at=now,
        property_address="Test Address",
        property_latitude=-25.754,
        property_longitude=28.231,
    )


@pytest.mark.asyncio
async def test_list_incidents_forwards_filters():
    neighbourhood_id = uuid4()
    camera_id = uuid4()
    claims = {"id": str(uuid4())}
    db = MagicMock()

    now = datetime.now(timezone.utc)
    alert = make_alert_response(uuid4())

    summary = IncidentSummaryRes(
        id=uuid4(),
        detection_type="WEAPON_DETECTED",
        started_at=now,
        last_seen_at=now,
        alert_count=1,
        representative_alert_id=alert.id,
        representative_alert=alert,
    )

    start_date = now.replace(hour=0, minute=0, second=0)
    end_date = now.replace(hour=23, minute=59, second=59)

    with patch(
        "app.api.controllers.incidents.list_incidents_handler",
        new=AsyncMock(return_value=([summary], 1)),
    ) as handler:
        response = await list_incidents(
            neighbourhood_id=neighbourhood_id,
            db=db,
            claims=claims,
            status_filter="ACKNOWLEDGED",
            camera_id=camera_id,
            detection_type="WEAPON_DETECTED",
            start_date=start_date,
            end_date=end_date,
            limit=10,
            offset=20,
        )

    assert response.status == 200
    assert response.data == [summary]
    assert response.pagination.total == 1
    assert response.pagination.limit == 10
    assert response.pagination.offset == 20
    assert response.pagination.has_more is False

    handler.assert_awaited_once_with(
        neighbourhood_id=neighbourhood_id,
        db=db,
        claims=claims,
        status_filter="ACKNOWLEDGED",
        camera_id=camera_id,
        detection_type="WEAPON_DETECTED",
        start_date=start_date,
        end_date=end_date,
        limit=10,
        offset=20,
    )


@pytest.mark.asyncio
async def test_list_incidents_sets_has_more_when_pages_remain():
    neighbourhood_id = uuid4()
    claims = {"id": str(uuid4())}
    db = MagicMock()

    now = datetime.now(timezone.utc)
    alert = make_alert_response(uuid4())

    summary = IncidentSummaryRes(
        id=uuid4(),
        detection_type="WEAPON_DETECTED",
        started_at=now,
        last_seen_at=now,
        alert_count=1,
        representative_alert_id=alert.id,
        representative_alert=alert,
    )

    with patch(
        "app.api.controllers.incidents.list_incidents_handler",
        new=AsyncMock(return_value=([summary], 25)),
    ):
        response = await list_incidents(
            neighbourhood_id=neighbourhood_id,
            db=db,
            claims=claims,
            limit=10,
            offset=0,
        )

    assert response.pagination.total == 25
    assert response.pagination.limit == 10
    assert response.pagination.offset == 0
    assert response.pagination.has_more is True


@pytest.mark.asyncio
async def test_get_incident_forwards_id_and_authorization():
    incident_id = uuid4()
    claims = {"id": str(uuid4())}
    db = MagicMock()

    now = datetime.now(timezone.utc)
    alert_one = make_alert_response(uuid4())
    alert_two = make_alert_response(uuid4())

    detail = IncidentDetailRes(
        id=incident_id,
        detection_type="WEAPON_DETECTED",
        started_at=now,
        last_seen_at=now,
        alert_count=2,
        alerts=[alert_one, alert_two],
    )

    with patch(
        "app.api.controllers.incidents.get_incident_handler",
        new=AsyncMock(return_value=detail),
    ) as handler:
        response = await get_incident(
            incident_id=incident_id,
            db=db,
            claims=claims,
        )

    assert response.status == 200
    assert response.data == detail

    handler.assert_awaited_once_with(
        incident_id=incident_id,
        db=db,
        claims=claims,
    )