from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.notification import list_notifications_for_alert


ALERT_ID = uuid4()
CAMERA_ID = uuid4()
USER_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()


def make_result(*, scalar=None, rows=None):
    result = Mock()
    result.scalar_one_or_none.return_value = scalar
    result.scalars.return_value.all.return_value = rows or []
    return result


def make_alert():
    return SimpleNamespace(
        id=ALERT_ID,
        camera_id=CAMERA_ID,
    )


def make_camera(neighbourhood_id=NEIGHBOURHOOD_ID):
    return SimpleNamespace(
        id=CAMERA_ID,
        neighbourhood_id=neighbourhood_id,
    )


def make_notification(
    *,
    channel="EMAIL",
    status="SENT",
):
    return SimpleNamespace(
        id=uuid4(),
        alert_id=ALERT_ID,
        user_id=USER_ID,
        channel=channel,
        status=status,
        sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_list_notifications_rejects_unauthorized_role():
    db = Mock()
    claims = {
        "custom:role": "RESIDENT",
        "custom:neighbourhood_id": str(NEIGHBOURHOOD_ID),
    }

    with pytest.raises(HTTPException) as exc_info:
        await list_notifications_for_alert(
            alert_id=ALERT_ID,
            db=db,
            claims=claims,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions"
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_list_notifications_rejects_missing_role():
    db = Mock()
    claims = {
        "custom:neighbourhood_id": str(NEIGHBOURHOOD_ID),
    }

    with pytest.raises(HTTPException) as exc_info:
        await list_notifications_for_alert(
            alert_id=ALERT_ID,
            db=db,
            claims=claims,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions"
    db.execute.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role",
    [
        "NEIGHBOURHOOD_ADMIN",
        "SYSTEM_ADMIN",
        "SECURITY_OFFICER",
    ],
)
async def test_list_notifications_allows_authorized_roles(role):
    alert = make_alert()
    camera = make_camera()
    notifications = [
        make_notification(channel="EMAIL"),
        make_notification(channel="WHATSAPP", status="FAILED"),
    ]

    db = Mock()
    db.execute.side_effect = [
        make_result(scalar=alert),
        make_result(scalar=camera),
        make_result(rows=notifications),
    ]

    claims = {
        "custom:role": role,
        "custom:neighbourhood_id": str(NEIGHBOURHOOD_ID),
    }

    response = await list_notifications_for_alert(
        alert_id=ALERT_ID,
        db=db,
        claims=claims,
    )

    assert response.status == 200
    assert response.message is None
    assert len(response.data) == 2

    assert response.data[0].id == notifications[0].id
    assert response.data[0].alert_id == ALERT_ID
    assert response.data[0].user_id == USER_ID
    assert response.data[0].channel == "EMAIL"
    assert response.data[0].status == "SENT"

    assert response.data[1].channel == "WHATSAPP"
    assert response.data[1].status == "FAILED"

    assert db.execute.call_count == 3


@pytest.mark.asyncio
async def test_list_notifications_returns_empty_data_when_no_notifications_exist():
    db = Mock()
    db.execute.side_effect = [
        make_result(scalar=make_alert()),
        make_result(scalar=make_camera()),
        make_result(rows=[]),
    ]

    claims = {
        "custom:role": "SECURITY_OFFICER",
        "custom:neighbourhood_id": str(NEIGHBOURHOOD_ID),
    }

    response = await list_notifications_for_alert(
        alert_id=ALERT_ID,
        db=db,
        claims=claims,
    )

    assert response.status == 200
    assert response.data == []
    assert db.execute.call_count == 3


@pytest.mark.asyncio
async def test_list_notifications_returns_404_when_alert_does_not_exist():
    db = Mock()
    db.execute.return_value = make_result(scalar=None)

    claims = {
        "custom:role": "NEIGHBOURHOOD_ADMIN",
        "custom:neighbourhood_id": str(NEIGHBOURHOOD_ID),
    }

    with pytest.raises(HTTPException) as exc_info:
        await list_notifications_for_alert(
            alert_id=ALERT_ID,
            db=db,
            claims=claims,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Alert not found"
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_list_notifications_returns_403_when_camera_does_not_exist():
    db = Mock()
    db.execute.side_effect = [
        make_result(scalar=make_alert()),
        make_result(scalar=None),
    ]

    claims = {
        "custom:role": "SECURITY_OFFICER",
        "custom:neighbourhood_id": str(NEIGHBOURHOOD_ID),
    }

    with pytest.raises(HTTPException) as exc_info:
        await list_notifications_for_alert(
            alert_id=ALERT_ID,
            db=db,
            claims=claims,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Not authorised for this alert"
    assert db.execute.call_count == 2


@pytest.mark.asyncio
async def test_list_notifications_returns_403_when_camera_is_in_another_neighbourhood():
    alert = make_alert()
    camera = make_camera(neighbourhood_id=uuid4())

    db = Mock()
    db.execute.side_effect = [
        make_result(scalar=alert),
        make_result(scalar=camera),
    ]

    claims = {
        "custom:role": "NEIGHBOURHOOD_ADMIN",
        "custom:neighbourhood_id": str(NEIGHBOURHOOD_ID),
    }

    with pytest.raises(HTTPException) as exc_info:
        await list_notifications_for_alert(
            alert_id=ALERT_ID,
            db=db,
            claims=claims,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Not authorised for this alert"
    assert db.execute.call_count == 2


@pytest.mark.asyncio
async def test_list_notifications_compares_neighbourhood_ids_as_strings():
    alert = make_alert()
    camera = make_camera(neighbourhood_id=NEIGHBOURHOOD_ID)

    db = Mock()
    db.execute.side_effect = [
        make_result(scalar=alert),
        make_result(scalar=camera),
        make_result(rows=[]),
    ]

    claims = {
        "custom:role": "SECURITY_OFFICER",
        "custom:neighbourhood_id": str(NEIGHBOURHOOD_ID),
    }

    response = await list_notifications_for_alert(
        alert_id=ALERT_ID,
        db=db,
        claims=claims,
    )

    assert response.status == 200
    assert response.data == []