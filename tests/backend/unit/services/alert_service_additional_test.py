import base64
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from botocore.exceptions import BotoCoreError
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.alert import DetectionType
from app.models.neighbourhood_user import NeighbourhoodRole
from app.schemas.alert import (
    AlertCreate,
    CreateInternalAlertRequest,
    TimePeriod,
    TrendBucket,
    TrendDirection,
    TrendGroupBy,
    UpdateAlertClipRequest,
)
from app.services import alert_service as service


ALERT_ID = uuid4()
CAMERA_ID = uuid4()
PROPERTY_ID = uuid4()
USER_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()
CREDENTIAL_PROPERTY_ID = PROPERTY_ID
FRAME_TIMESTAMP = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_result(
    *,
    scalar=None,
    scalar_one=None,
    one=None,
    rows=None,
):
    result = Mock()
    result.scalar_one_or_none.return_value = scalar
    result.scalar_one.return_value = scalar_one
    result.one_or_none.return_value = one
    result.scalars.return_value.all.return_value = rows or []
    result.all.return_value = rows or []
    return result


def make_property(
    *,
    neighbourhood_id=NEIGHBOURHOOD_ID,
    address="123 Watchdog Street",
    latitude=-25.754,
    longitude=28.231,
):
    return SimpleNamespace(
        id=PROPERTY_ID,
        neighbourhood_id=neighbourhood_id,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )


def make_camera(
    *,
    property_obj=None,
):
    return SimpleNamespace(
        id=CAMERA_ID,
        property_id=PROPERTY_ID,
        property=property_obj or make_property(),
    )


def make_alert(
    *,
    status="OPEN",
    detection_type=DetectionType.HUMAN_PRESENCE,
    camera=None,
):
    property_obj = make_property()
    return SimpleNamespace(
        id=ALERT_ID,
        camera_id=CAMERA_ID,
        frame_timestamp=FRAME_TIMESTAMP,
        detection_type=detection_type,
        confidence_score=0.85,
        thumbnail_url="https://example.com/thumbnail.jpg",
        clip_s3_key=None,
        clip_expires_at=None,
        processed=False,
        status=status,
        resolved_by=None,
        resolved_at=None,
        created_at=FRAME_TIMESTAMP,
        camera=camera or make_camera(property_obj=property_obj),
    )


def make_claims():
    return {
        "id": str(USER_ID),
        "sub": "cognito-sub-123",
    }


def make_db():
    db = Mock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


def make_alert_create(
    *,
    neighbourhood_id=NEIGHBOURHOOD_ID,
):
    return AlertCreate(
        camera_id=CAMERA_ID,
        neighbourhood_id=neighbourhood_id,
        detection_type="HUMAN_PRESENCE",
        confidence=0.85,
        timestamp=FRAME_TIMESTAMP,
        thumbnail_url="https://example.com/thumbnail.jpg",
    )


def make_internal_alert_request(
    *,
    camera_id=str(CAMERA_ID),
    detection_type="HUMAN_PRESENCE",
    frame_timestamp="2026-01-01T12:00:00+00:00",
):
    return CreateInternalAlertRequest(
        camera_id=camera_id,
        detection_type=detection_type,
        confidence_score=0.91,
        thumbnail_url="https://example.com/thumbnail.jpg",
        frame_timestamp=frame_timestamp,
    )


def make_edge_credential():
    return SimpleNamespace(
        property_id=CREDENTIAL_PROPERTY_ID,
    )


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def test_safe_optional_coordinate_accepts_finite_numbers():
    assert service._safe_optional_coordinate(10) == 10.0
    assert service._safe_optional_coordinate(10.5) == 10.5


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        "10.5",
        float("inf"),
        float("-inf"),
        float("nan"),
        object(),
    ],
)
def test_safe_optional_coordinate_returns_none_for_invalid_values(value):
    assert service._safe_optional_coordinate(value) is None


def test_build_alert_response_includes_property_location():
    alert = make_alert(
        detection_type=DetectionType.WEAPON_DETECTED,
    )

    response = service._build_alert_res(alert)

    assert response.id == ALERT_ID
    assert response.camera_id == CAMERA_ID
    assert response.detection_type == DetectionType.WEAPON_DETECTED.value
    assert response.confidence_score == 0.85
    assert response.property_address == "123 Watchdog Street"
    assert response.property_latitude == -25.754
    assert response.property_longitude == 28.231


def test_build_alert_response_converts_non_string_property_address_to_none():
    property_obj = make_property(
        address=Mock(),
        latitude="invalid",
        longitude=True,
    )
    alert = make_alert(
        camera=make_camera(property_obj=property_obj),
    )

    response = service._build_alert_res(alert)

    assert response.property_address is None
    assert response.property_latitude is None
    assert response.property_longitude is None


@pytest.mark.parametrize(
    "detection_type,expected",
    [
        (DetectionType.WEAPON_DETECTED, True),
        (DetectionType.FALL_DETECTED, True),
        (DetectionType.HUMAN_PRESENCE, False),
    ],
)
def test_is_critical_alert(detection_type, expected):
    alert = make_alert(detection_type=detection_type)

    assert service._is_critical_alert(alert) is expected


def test_neighbourhood_admin_can_acknowledge_any_alert():
    alert = make_alert(
        detection_type=DetectionType.WEAPON_DETECTED,
    )
    membership = SimpleNamespace(
        role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
    )

    assert service._can_acknowledge_alert(
        alert,
        property_membership=None,
        neighbourhood_membership=membership,
    ) is True


def test_security_officer_can_acknowledge_critical_alert():
    alert = make_alert(
        detection_type=DetectionType.WEAPON_DETECTED,
    )
    membership = SimpleNamespace(
        role=NeighbourhoodRole.SECURITY_OFFICER,
    )

    assert service._can_acknowledge_alert(
        alert,
        property_membership=None,
        neighbourhood_membership=membership,
    ) is True


def test_security_officer_cannot_acknowledge_non_critical_alert():
    alert = make_alert(
        detection_type=DetectionType.HUMAN_PRESENCE,
    )
    membership = SimpleNamespace(
        role=NeighbourhoodRole.SECURITY_OFFICER,
    )

    assert service._can_acknowledge_alert(
        alert,
        property_membership=None,
        neighbourhood_membership=membership,
    ) is False


def test_property_admin_can_acknowledge_non_critical_alert():
    alert = make_alert(
        detection_type=DetectionType.HUMAN_PRESENCE,
    )
    property_membership = SimpleNamespace(is_admin=True)

    assert service._can_acknowledge_alert(
        alert,
        property_membership=property_membership,
        neighbourhood_membership=None,
    ) is True


def test_property_admin_cannot_acknowledge_critical_alert():
    alert = make_alert(
        detection_type=DetectionType.WEAPON_DETECTED,
    )
    property_membership = SimpleNamespace(is_admin=True)

    assert service._can_acknowledge_alert(
        alert,
        property_membership=property_membership,
        neighbourhood_membership=None,
    ) is False


def test_property_alert_statement_is_created():
    statement = service._property_alert_stmt(PROPERTY_ID)

    assert statement is not None


def test_neighbourhood_alert_statement_is_created():
    statement = service._neighbourhood_alert_stmt(NEIGHBOURHOOD_ID)

    assert statement is not None


# ---------------------------------------------------------------------------
# Neighbourhood membership and WebSocket recipients
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_require_neighbourhood_membership_rejects_missing_claim_id():
    db = make_db()

    with pytest.raises(HTTPException) as exc_info:
        await service._require_neighbourhood_membership(
            db=db,
            claims={},
            neighbourhood_id=NEIGHBOURHOOD_ID,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == service.NOT_AUTHENTICATED
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_require_neighbourhood_membership_rejects_invalid_claim_id():
    db = make_db()

    with pytest.raises(HTTPException) as exc_info:
        await service._require_neighbourhood_membership(
            db=db,
            claims={"id": "not-a-uuid"},
            neighbourhood_id=NEIGHBOURHOOD_ID,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == service.NOT_AUTHENTICATED
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_require_neighbourhood_membership_rejects_missing_membership():
    db = make_db()
    db.execute.return_value = make_result(scalar=None)

    with pytest.raises(HTTPException) as exc_info:
        await service._require_neighbourhood_membership(
            db=db,
            claims={"id": str(USER_ID)},
            neighbourhood_id=NEIGHBOURHOOD_ID,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == service.NOT_AUTHORISED
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_require_neighbourhood_membership_returns_membership():
    membership = SimpleNamespace(
        user_id=USER_ID,
        neighbourhood_id=NEIGHBOURHOOD_ID,
        role=NeighbourhoodRole.RESIDENT,
    )

    db = make_db()
    db.execute.return_value = make_result(scalar=membership)

    result = await service._require_neighbourhood_membership(
        db=db,
        claims={"id": str(USER_ID)},
        neighbourhood_id=NEIGHBOURHOOD_ID,
    )

    assert result is membership
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_neighbourhood_websocket_recipient_ids_returns_string_ids():
    user_id_one = uuid4()
    user_id_two = uuid4()

    db = make_db()
    result = Mock()
    result.scalars.return_value.all.return_value = [
        user_id_one,
        user_id_two,
    ]
    db.execute.return_value = result

    recipients = await service._get_neighbourhood_websocket_recipient_ids(
        db,
        NEIGHBOURHOOD_ID,
    )

    assert recipients == [
        str(user_id_one),
        str(user_id_two),
    ]
    db.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# Basic alert creation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_alert_persists_and_broadcasts_to_neighbourhood():
    alert = make_alert()
    db = make_db()

    with (
        patch(
            "app.services.alert_service.Alert",
            return_value=alert,
        ) as alert_model,
        patch(
            "app.services.alert_service._get_neighbourhood_websocket_recipient_ids",
            new=AsyncMock(return_value=["user-one", "user-two"]),
        ) as recipients,
        patch(
            "app.api.controllers.alert.broadcast",
            new=AsyncMock(),
        ) as broadcast,
    ):
        response = await service.create_alert(
            db,
            make_alert_create(),
        )

    assert response.id == ALERT_ID
    assert response.camera_id == CAMERA_ID
    assert response.status == "OPEN"
    assert response.created_at == FRAME_TIMESTAMP

    alert_model.assert_called_once_with(
        camera_id=CAMERA_ID,
        frame_timestamp=FRAME_TIMESTAMP,
        detection_type="HUMAN_PRESENCE",
        confidence_score=0.85,
        thumbnail_url="https://example.com/thumbnail.jpg",
        processed=False,
    )

    db.add.assert_called_once_with(alert)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(alert)

    recipients.assert_awaited_once_with(
        db,
        NEIGHBOURHOOD_ID,
    )

    broadcast.assert_awaited_once_with(
        ["user-one", "user-two"],
        {
            "event": "new_alert",
            "alert_id": str(ALERT_ID),
            "camera_id": str(CAMERA_ID),
            "detection_type": "HUMAN_PRESENCE",
            "confidence": 0.85,
        },
    )


@pytest.mark.asyncio
async def test_create_alert_skips_broadcast_without_neighbourhood():
    alert = make_alert()
    db = make_db()
    data = make_alert_create(neighbourhood_id=None)

    with (
        patch(
            "app.services.alert_service.Alert",
            return_value=alert,
        ),
        patch(
            "app.api.controllers.alert.broadcast",
            new=AsyncMock(),
        ) as broadcast,
        patch(
            "app.services.alert_service._get_neighbourhood_websocket_recipient_ids",
            new=AsyncMock(),
        ) as recipients,
    ):
        response = await service.create_alert(db, data)

    assert response.id == ALERT_ID
    broadcast.assert_not_awaited()
    recipients.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_alert_rolls_back_and_reraises_http_exception():
    db = make_db()
    error = HTTPException(
        status_code=400,
        detail="Invalid alert",
    )
    db.add.side_effect = error

    with pytest.raises(HTTPException) as exc_info:
        await service.create_alert(
            db,
            make_alert_create(),
        )

    assert exc_info.value is error
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_alert_rolls_back_and_wraps_unexpected_error():
    db = make_db()
    db.add.side_effect = RuntimeError("database failure")

    with pytest.raises(HTTPException) as exc_info:
        await service.create_alert(
            db,
            make_alert_create(),
        )

    assert exc_info.value.status_code == 500
    assert "Failed to create alert" in exc_info.value.detail
    assert "database failure" in exc_info.value.detail
    db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Property alert listing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_property_alerts_requires_property_id():
    db = make_db()

    with pytest.raises(HTTPException) as exc_info:
        await service.list_property_alerts_handler(
            property_id=None,
            db=db,
            claims=make_claims(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Property id is required"


@pytest.mark.asyncio
async def test_list_property_alerts_requires_database_session():
    with pytest.raises(HTTPException) as exc_info:
        await service.list_property_alerts_handler(
            property_id=PROPERTY_ID,
            db=None,
            claims=make_claims(),
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == service.NO_DATABASE_SESSION


@pytest.mark.asyncio
async def test_list_property_alerts_requires_claims():
    db = make_db()

    with pytest.raises(HTTPException) as exc_info:
        await service.list_property_alerts_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == service.NOT_AUTHENTICATED


@pytest.mark.asyncio
async def test_list_property_alerts_rejects_invalid_claim_id():
    db = make_db()

    with pytest.raises(HTTPException) as exc_info:
        await service.list_property_alerts_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims={"id": "invalid"},
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == service.NOT_AUTHENTICATED


@pytest.mark.asyncio
async def test_list_property_alerts_rejects_reversed_date_range():
    db = make_db()
    start_date = datetime(2026, 2, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(HTTPException) as exc_info:
        await service.list_property_alerts_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=make_claims(),
            start_date=start_date,
            end_date=end_date,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "start_date must be less than end_date"
    )


@pytest.mark.asyncio
async def test_list_property_alerts_returns_404_for_unknown_property():
    db = make_db()
    db.execute.return_value = make_result(scalar=None)

    with pytest.raises(HTTPException) as exc_info:
        await service.list_property_alerts_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=make_claims(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Property not found"


@pytest.mark.asyncio
async def test_list_property_alerts_rejects_user_without_property_access():
    db = make_db()
    db.execute.side_effect = [
        make_result(scalar=make_property()),
        make_result(scalar=None),
    ]

    with pytest.raises(HTTPException) as exc_info:
        await service.list_property_alerts_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=make_claims(),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "You do not have access to this property"
    )


@pytest.mark.asyncio
async def test_list_property_alerts_returns_paginated_alerts():
    property_obj = make_property()
    membership = SimpleNamespace(
        user_id=USER_ID,
        property_id=PROPERTY_ID,
    )
    alert = make_alert()

    count_result = make_result(scalar_one=1)

    db = make_db()
    db.execute.side_effect = [
        make_result(scalar=property_obj),
        make_result(scalar=membership),
        count_result,
        make_result(rows=[alert]),
    ]

    alerts, total = await service.list_property_alerts_handler(
        property_id=str(PROPERTY_ID),
        db=db,
        claims=make_claims(),
        status_filter="OPEN",
        camera_id=CAMERA_ID,
        detection_type=DetectionType.HUMAN_PRESENCE.value,
        start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 1, 2, tzinfo=timezone.utc),
        limit=10,
        offset=5,
    )

    assert total == 1
    assert len(alerts) == 1
    assert alerts[0].id == ALERT_ID
    assert alerts[0].camera_id == CAMERA_ID
    assert db.execute.await_count == 4


@pytest.mark.asyncio
async def test_list_property_alerts_rolls_back_on_integrity_error():
    db = make_db()
    db.execute.side_effect = IntegrityError(
        "statement",
        {},
        RuntimeError("database failure"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.list_property_alerts_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=make_claims(),
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to list property alerts"
    db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Trend helpers and trend retrieval
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "time_period",
    [
        TimePeriod.WEEK,
        TimePeriod.MONTH,
        TimePeriod.THREE_MONTHS,
        TimePeriod.SIX_MONTHS,
        TimePeriod.YEAR,
    ],
)
def test_resolve_start_date_returns_date_for_supported_periods(time_period):
    result = service._resolve_start_date(time_period)

    assert isinstance(result, date)


def test_resolve_start_date_returns_none_for_missing_period():
    assert service._resolve_start_date(None) is None


@pytest.mark.parametrize(
    "counts,expected",
    [
        ([5], TrendDirection.STABLE),
        ([5, 5], TrendDirection.STABLE),
        ([10, 2], TrendDirection.DOWN),
        ([2, 10], TrendDirection.UP),
        ([3, 4, 3, 4], TrendDirection.STABLE),
    ],
)
def test_compute_trend_direction(counts, expected):
    buckets = [
        TrendBucket(
            period=datetime(2026, 1, index + 1),
            count=count,
        )
        for index, count in enumerate(counts)
    ]

    assert service._compute_trend_direction(buckets) == expected


@pytest.mark.asyncio
async def test_get_trends_requires_database_session():
    with pytest.raises(HTTPException) as exc_info:
        await service.get_trends_handler(
            neighbourhood_id=NEIGHBOURHOOD_ID,
            db=None,
            claims=make_claims(),
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == service.NO_DATABASE_SESSION


@pytest.mark.asyncio
async def test_get_trends_requires_claims():
    db = make_db()

    with pytest.raises(HTTPException) as exc_info:
        await service.get_trends_handler(
            neighbourhood_id=NEIGHBOURHOOD_ID,
            db=db,
            claims=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == service.NOT_AUTHENTICATED


@pytest.mark.asyncio
async def test_get_trends_propagates_membership_error():
    db = make_db()
    error = HTTPException(
        status_code=403,
        detail=service.NOT_AUTHORISED,
    )

    with patch(
        "app.services.alert_service._require_neighbourhood_membership",
        new=AsyncMock(side_effect=error),
    ) as membership:
        with pytest.raises(HTTPException) as exc_info:
            await service.get_trends_handler(
                neighbourhood_id=NEIGHBOURHOOD_ID,
                db=db,
                claims=make_claims(),
            )

    assert exc_info.value is error
    membership.assert_awaited_once_with(
        db,
        make_claims(),
        NEIGHBOURHOOD_ID,
    )


@pytest.mark.asyncio
async def test_get_trends_builds_buckets_and_calculates_total():
    db = make_db()

    membership = SimpleNamespace(
        role=NeighbourhoodRole.RESIDENT,
    )

    row_one = SimpleNamespace(
        bucket=datetime(2026, 1, 1),
        count=2,
    )
    row_two = SimpleNamespace(
        bucket=datetime(2026, 1, 2),
        count=5,
    )

    db.execute.return_value = make_result(
        rows=[row_one, row_two],
    )

    expected_response = Mock()

    with (
        patch(
            "app.services.alert_service._require_neighbourhood_membership",
            new=AsyncMock(return_value=membership),
        ),
        patch(
            "app.services.alert_service.TrendData",
            return_value=expected_response,
        ) as trend_data,
    ):
        response = await service.get_trends_handler(
            neighbourhood_id=NEIGHBOURHOOD_ID,
            db=db,
            claims=make_claims(),
            group_by=TrendGroupBy.DAY,
            time_period=TimePeriod.MONTH,
            incident_type=DetectionType.HUMAN_PRESENCE.value,
            camera_id=CAMERA_ID,
        )

    assert response is expected_response

    trend_data.assert_called_once()
    kwargs = trend_data.call_args.kwargs

    assert kwargs["total_count"] == 7
    assert kwargs["trend_direction"] == TrendDirection.UP
    assert len(kwargs["buckets"]) == 2
    assert kwargs["buckets"][0].count == 2
    assert kwargs["buckets"][1].count == 5


@pytest.mark.asyncio
async def test_get_trends_rolls_back_on_integrity_error():
    db = make_db()
    db.execute.side_effect = IntegrityError(
        "statement",
        {},
        RuntimeError("database failure"),
    )

    with patch(
        "app.services.alert_service._require_neighbourhood_membership",
        new=AsyncMock(),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await service.get_trends_handler(
                neighbourhood_id=NEIGHBOURHOOD_ID,
                db=db,
                claims=make_claims(),
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to fetch trend data"
    db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Edge-agent alert creation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_alert_for_agent_rejects_invalid_camera_uuid():
    db = make_db()
    body = make_internal_alert_request(
        camera_id="not-a-uuid",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_alert_for_agent_handler(
            body,
            db,
            make_edge_credential(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "camera_id is not a valid UUID"
    )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_alert_for_agent_rejects_invalid_timestamp():
    db = make_db()
    body = make_internal_alert_request(
        frame_timestamp="not-a-timestamp",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_alert_for_agent_handler(
            body,
            db,
            make_edge_credential(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "frame_timestamp is not a valid ISO datetime"
    )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_alert_for_agent_rejects_unknown_camera():
    db = make_db()
    db.execute.return_value = make_result(scalar=None)

    body = make_internal_alert_request()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_alert_for_agent_handler(
            body,
            db,
            make_edge_credential(),
        )

    assert exc_info.value.status_code == 404
    assert str(CAMERA_ID) in exc_info.value.detail
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_alert_for_agent_maps_known_detection_label():
    db = make_db()
    db.execute.return_value = make_result(
        scalar=make_camera(),
    )

    alert = SimpleNamespace(
        id=ALERT_ID,
        camera_id=CAMERA_ID,
        detection_type=DetectionType.WEAPON_DETECTED,
    )

    body = make_internal_alert_request(
        detection_type="gun",
    )

    with patch(
        "app.services.alert_service.Alert",
        return_value=alert,
    ) as alert_model:
        response = await service.create_alert_for_agent_handler(
            body,
            db,
            make_edge_credential(),
        )

    assert response.alert_id == ALERT_ID
    alert_model.assert_called_once()

    call_kwargs = alert_model.call_args.kwargs
    assert call_kwargs["camera_id"] == CAMERA_ID
    assert call_kwargs["detection_type"] == DetectionType.WEAPON_DETECTED
    assert call_kwargs["confidence_score"] == 0.91
    assert call_kwargs["processed"] is True
    assert call_kwargs["status"] == "OPEN"

    db.add.assert_called_once_with(alert)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(alert)


@pytest.mark.asyncio
async def test_create_alert_for_agent_uses_default_detection_for_unknown_label():
    db = make_db()
    db.execute.return_value = make_result(
        scalar=make_camera(),
    )

    alert = SimpleNamespace(
        id=ALERT_ID,
        camera_id=CAMERA_ID,
        detection_type=DetectionType.WEAPON_DETECTED,
    )

    body = make_internal_alert_request(
        detection_type="unknown-label",
    )

    with patch(
        "app.services.alert_service.Alert",
        return_value=alert,
    ) as alert_model:
        response = await service.create_alert_for_agent_handler(
            body,
            db,
            make_edge_credential(),
        )

    assert response.alert_id == ALERT_ID
    assert (
        alert_model.call_args.kwargs["detection_type"]
        == DetectionType.WEAPON_DETECTED
    )


@pytest.mark.asyncio
async def test_create_alert_for_agent_uses_current_time_without_timestamp():
    db = make_db()
    db.execute.return_value = make_result(
        scalar=make_camera(),
    )

    alert = SimpleNamespace(
        id=ALERT_ID,
        camera_id=CAMERA_ID,
        detection_type=DetectionType.HUMAN_PRESENCE,
    )

    body = make_internal_alert_request(
        frame_timestamp=None,
    )

    with patch(
        "app.services.alert_service.Alert",
        return_value=alert,
    ) as alert_model:
        await service.create_alert_for_agent_handler(
            body,
            db,
            make_edge_credential(),
        )

    frame_timestamp = alert_model.call_args.kwargs["frame_timestamp"]
    assert isinstance(frame_timestamp, datetime)
    assert frame_timestamp.tzinfo is not None


@pytest.mark.asyncio
async def test_create_alert_for_agent_wraps_unexpected_database_error():
    db = make_db()
    db.execute.side_effect = RuntimeError("database unavailable")

    body = make_internal_alert_request()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_alert_for_agent_handler(
            body,
            db,
            make_edge_credential(),
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to create alert"
    db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Edge-agent clip metadata updates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_alert_clip_rejects_invalid_alert_id():
    db = make_db()
    body = UpdateAlertClipRequest(
        clip_s3_key="clips/example.mp4",
        clip_expires_at="2026-01-08T12:00:00+00:00",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_alert_clip_for_agent_handler(
            "invalid-alert-id",
            body,
            make_edge_credential(),
            db,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == service.ALERT_ID_INVALID
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_alert_clip_rejects_invalid_expiry_datetime():
    db = make_db()
    body = UpdateAlertClipRequest(
        clip_s3_key="clips/example.mp4",
        clip_expires_at="invalid-date",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_alert_clip_for_agent_handler(
            str(ALERT_ID),
            body,
            make_edge_credential(),
            db,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "clip_expires_at is not a valid ISO datetime"
    )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_alert_clip_returns_404_for_unknown_alert():
    db = make_db()
    db.execute.return_value = make_result(scalar=None)

    body = UpdateAlertClipRequest(
        clip_s3_key="clips/example.mp4",
        clip_expires_at="2026-01-08T12:00:00+00:00",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_alert_clip_for_agent_handler(
            str(ALERT_ID),
            body,
            make_edge_credential(),
            db,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == service.ALERT_NOT_FOUND


@pytest.mark.asyncio
async def test_update_alert_clip_updates_metadata_and_commits():
    alert = make_alert()
    db = make_db()
    db.execute.return_value = make_result(scalar=alert)

    body = UpdateAlertClipRequest(
        clip_s3_key="clips/updated.mp4",
        clip_expires_at="2026-01-08T12:00:00+00:00",
    )

    response = await service.update_alert_clip_for_agent_handler(
        str(ALERT_ID),
        body,
        make_edge_credential(),
        db,
    )

    assert response.alert_id == ALERT_ID
    assert response.clip_s3_key == "clips/updated.mp4"
    assert response.clip_expires_at == datetime(
        2026,
        1,
        8,
        12,
        0,
        tzinfo=timezone.utc,
    )

    assert alert.clip_s3_key == "clips/updated.mp4"
    assert alert.clip_expires_at == datetime(
        2026,
        1,
        8,
        12,
        0,
        tzinfo=timezone.utc,
    )

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(alert)


@pytest.mark.asyncio
async def test_update_alert_clip_reraises_unexpected_error():
    db = make_db()
    db.execute.side_effect = RuntimeError("database unavailable")

    body = UpdateAlertClipRequest(
        clip_s3_key="clips/example.mp4",
        clip_expires_at="2026-01-08T12:00:00+00:00",
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        await service.update_alert_clip_for_agent_handler(
            str(ALERT_ID),
            body,
            make_edge_credential(),
            db,
        )


# ---------------------------------------------------------------------------
# Edge-agent S3 clip uploads
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_alert_clip_rejects_unconfigured_storage():
    db = make_db()

    with patch.object(service, "S3_BUCKET_NAME", ""):
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_alert_clip_for_agent_handler(
                str(ALERT_ID),
                b"clip-data",
                "video/mp4",
                make_edge_credential(),
                db,
            )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == (
        "Clip storage has not been configured."
    )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_alert_clip_rejects_empty_clip():
    db = make_db()

    with patch.object(service, "S3_BUCKET_NAME", "watchdog-clips"):
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_alert_clip_for_agent_handler(
                str(ALERT_ID),
                b"",
                "video/mp4",
                make_edge_credential(),
                db,
            )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "The uploaded clip is empty."
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_alert_clip_rejects_clip_over_50_mib():
    db = make_db()
    oversized_clip = b"x" * (50 * 1024 * 1024 + 1)

    with patch.object(service, "S3_BUCKET_NAME", "watchdog-clips"):
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_alert_clip_for_agent_handler(
                str(ALERT_ID),
                oversized_clip,
                "video/mp4",
                make_edge_credential(),
                db,
            )

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == (
        "Clip exceeds the 50 MiB upload limit."
    )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_alert_clip_rejects_invalid_alert_id():
    db = make_db()

    with patch.object(service, "S3_BUCKET_NAME", "watchdog-clips"):
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_alert_clip_for_agent_handler(
                "invalid-alert-id",
                b"clip-data",
                "video/mp4",
                make_edge_credential(),
                db,
            )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == service.ALERT_ID_INVALID
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_alert_clip_returns_404_for_unknown_alert():
    db = make_db()
    db.execute.return_value = make_result(scalar=None)

    with patch.object(service, "S3_BUCKET_NAME", "watchdog-clips"):
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_alert_clip_for_agent_handler(
                str(ALERT_ID),
                b"clip-data",
                "video/mp4",
                make_edge_credential(),
                db,
            )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == service.ALERT_NOT_FOUND


@pytest.mark.asyncio
async def test_upload_alert_clip_uploads_to_s3_and_links_alert():
    alert = make_alert()
    db = make_db()
    db.execute.return_value = make_result(scalar=alert)

    s3_client = Mock()
    to_thread = AsyncMock()

    with (
        patch.object(service, "S3_BUCKET_NAME", "watchdog-clips"),
        patch.object(
            service,
            "_s3_client",
            return_value=s3_client,
        ),
        patch.object(
            service,
            "_clip_s3_key",
            return_value="clips/test-alert.mp4",
        ),
        patch.object(
            service.asyncio,
            "to_thread",
            new=to_thread,
        ),
    ):
        response = await service.upload_alert_clip_for_agent_handler(
            str(ALERT_ID),
            b"clip-data",
            "video/mp4",
            make_edge_credential(),
            db,
        )

    assert response.alert_id == ALERT_ID
    assert response.clip_s3_key == "clips/test-alert.mp4"
    assert response.clip_expires_at is not None

    assert alert.clip_s3_key == "clips/test-alert.mp4"
    assert alert.clip_expires_at is not None

    to_thread.assert_awaited_once()
    assert to_thread.await_args.args[0] is s3_client.put_object
    assert to_thread.await_args.kwargs == {
        "Bucket": "watchdog-clips",
        "Key": "clips/test-alert.mp4",
        "Body": b"clip-data",
        "ContentType": "video/mp4",
        "ServerSideEncryption": "AES256",
    }

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(alert)


@pytest.mark.asyncio
async def test_upload_alert_clip_defaults_missing_content_type_to_mp4():
    alert = make_alert()
    db = make_db()
    db.execute.return_value = make_result(scalar=alert)

    s3_client = Mock()
    to_thread = AsyncMock()

    with (
        patch.object(service, "S3_BUCKET_NAME", "watchdog-clips"),
        patch.object(service, "_s3_client", return_value=s3_client),
        patch.object(
            service,
            "_clip_s3_key",
            return_value="clips/test-alert.mp4",
        ),
        patch.object(
            service.asyncio,
            "to_thread",
            new=to_thread,
        ),
    ):
        await service.upload_alert_clip_for_agent_handler(
            str(ALERT_ID),
            b"clip-data",
            None,
            make_edge_credential(),
            db,
        )

    assert to_thread.await_args.kwargs["ContentType"] == "video/mp4"


@pytest.mark.asyncio
async def test_upload_alert_clip_translates_s3_failure_to_503():
    alert = make_alert()
    db = make_db()
    db.execute.return_value = make_result(scalar=alert)

    s3_client = Mock()
    to_thread = AsyncMock(
        side_effect=BotoCoreError(error_msg="temporary S3 failure")
    )

    with (
        patch.object(service, "S3_BUCKET_NAME", "watchdog-clips"),
        patch.object(service, "_s3_client", return_value=s3_client),
        patch.object(
            service,
            "_clip_s3_key",
            return_value="clips/test-alert.mp4",
        ),
        patch.object(
            service.asyncio,
            "to_thread",
            new=to_thread,
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_alert_clip_for_agent_handler(
                str(ALERT_ID),
                b"clip-data",
                "video/mp4",
                make_edge_credential(),
                db,
            )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Could not store clip in S3."
    db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Agent alert lookup and chunked clip reading
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_alert_for_agent_returns_none_when_not_found():
    db = make_db()
    db.execute.return_value = make_result(scalar=None)

    result = await service.get_alert_for_agent(
        str(ALERT_ID),
        make_edge_credential(),
        db,
    )

    assert result is None
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_alert_for_agent_rejects_invalid_uuid():
    db = make_db()

    with pytest.raises(HTTPException) as exc_info:
        await service.get_alert_for_agent(
            "invalid-alert-id",
            make_edge_credential(),
            db,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == service.ALERT_ID_INVALID
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_clip_with_limit_combines_chunks():
    clip = Mock()
    clip.read = AsyncMock(
        side_effect=[
            b"first-",
            b"second",
            b"",
        ]
    )

    result = await service._read_clip_with_limit(
        clip,
        max_bytes=100,
    )

    assert result == b"first-second"
    assert clip.read.await_count == 3


@pytest.mark.asyncio
async def test_read_clip_with_limit_rejects_oversized_upload():
    clip = Mock()
    clip.read = AsyncMock(
        side_effect=[
            b"x" * 6,
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        await service._read_clip_with_limit(
            clip,
            max_bytes=5,
        )

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == (
        "Clip exceeds 5MB upload limit"
    )