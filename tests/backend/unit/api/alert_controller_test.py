from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import WebSocketDisconnect
import pytest

from app.api.controllers.alert import (
    alert_websocket,
    get_alert_distance,
    get_alert_property_route,
    get_alert_tracking_timeline,
    get_critical_alerts_map,
    get_unlocated_critical_alerts,
)

from app.schemas.alert import (
    AlertDistanceData,
    AlertRouteData,
    CriticalAlertMapData,
    UnlocatedCriticalAlertsData,
)
from app.schemas.tracking import TrackingTimelineResponse


@pytest.mark.asyncio
async def test_get_critical_alerts_map_delegates_to_handler():
    neighbourhood_id = uuid4()
    db = MagicMock()
    claims = {"sub": "test-user"}

    data = CriticalAlertMapData(
        alerts=[],
        last_updated=datetime.now(timezone.utc),
    )

    with patch(
        "app.api.controllers.alert."
        "get_critical_alerts_map_handler",
        new=AsyncMock(return_value=data),
    ) as handler:
        response = await get_critical_alerts_map(
            neighbourhood_id,
            db,
            claims,
        )

    assert response.status == 200
    assert response.data == data

    handler.assert_awaited_once_with(
        neighbourhood_id=neighbourhood_id,
        db=db,
        claims=claims,
    )


@pytest.mark.asyncio
async def test_get_unlocated_alerts_delegates_to_handler():
    neighbourhood_id = uuid4()
    db = MagicMock()
    claims = {"sub": "test-user"}

    data = UnlocatedCriticalAlertsData(
        alerts=[],
        last_updated=datetime.now(timezone.utc),
    )

    with patch(
        "app.api.controllers.alert."
        "get_unlocated_critical_alerts_handler",
        new=AsyncMock(return_value=data),
    ) as handler:
        response = await get_unlocated_critical_alerts(
            neighbourhood_id,
            db,
            claims,
        )

    assert response.status == 200
    assert response.data == data

    handler.assert_awaited_once_with(
        neighbourhood_id=neighbourhood_id,
        db=db,
        claims=claims,
    )


@pytest.mark.asyncio
async def test_alert_websocket_rejects_token_without_subject():
    websocket = MagicMock()
    websocket.close = AsyncMock()

    db = MagicMock()
    db.execute = AsyncMock()

    with patch(
        "app.api.controllers.alert.verify_jwt",
        return_value={},
    ):
        await alert_websocket(
            websocket=websocket,
            neighbourhood_id=uuid4(),
            db=db,
            token="invalid-token",
        )

    websocket.close.assert_awaited_once_with(
        code=1008,
    )
    websocket.accept.assert_not_called()
    db.execute.assert_not_awaited()

@pytest.mark.asyncio
async def test_alert_websocket_registers_authorised_user():
    neighbourhood_id = uuid4()

    user = MagicMock()
    user.id = uuid4()

    membership = MagicMock()

    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user

    membership_result = MagicMock()
    membership_result.scalar_one_or_none.return_value = (
        membership
    )

    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            user_result,
            membership_result,
        ]
    )

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()
    websocket.receive_text = AsyncMock(
        side_effect=WebSocketDisconnect(
            code=1000
        )
    )

    with (
        patch(
            "app.api.controllers.alert.verify_jwt",
            return_value={
                "sub": "cognito-user",
            },
        ),
        patch(
            "app.api.controllers.alert."
            "register_connection",
        ) as register,
        patch(
            "app.api.controllers.alert."
            "remove_connection",
        ) as remove,
    ):
        await alert_websocket(
            websocket=websocket,
            neighbourhood_id=neighbourhood_id,
            db=db,
            token="valid-token",
        )

    websocket.accept.assert_awaited_once()
    register.assert_called_once_with(
        str(user.id),
        websocket,
    )
    remove.assert_called_once_with(
        str(user.id),
        websocket,
    )


@pytest.mark.asyncio
async def test_get_alert_distance_delegates_to_handler():
    property_id = uuid4()
    db = MagicMock()
    claims = {"sub": "officer-sub"}

    data = AlertDistanceData(
        property_id=property_id,
        property_address="123 Test Street",
        property_latitude=-25.7479,
        property_longitude=28.2293,
        officer_latitude=-25.7600,
        officer_longitude=28.2100,
        distance_metres=2500,
        officer_location_updated_at=(
            datetime.now(timezone.utc)
        ),
    )

    with patch(
        "app.api.controllers.alert."
        "calculate_property_distance_handler",
        new=AsyncMock(return_value=data),
    ) as handler:
        response = await get_alert_distance(
            property_id,
            db,
            claims,
        )

    assert response.status == 200
    assert response.data == data

    handler.assert_awaited_once_with(
        property_id=property_id,
        db=db,
        claims=claims,
    )


@pytest.mark.asyncio
async def test_get_alert_route_delegates_to_handler():
    property_id = uuid4()
    db = MagicMock()
    claims = {"sub": "officer-sub"}

    data = AlertRouteData(
        property_id=property_id,
        property_address="123 Test Street",
        property_latitude=-25.7479,
        property_longitude=28.2293,
        officer_latitude=-25.7600,
        officer_longitude=28.2100,
        distance_metres=2500,
        officer_location_updated_at=(
            datetime.now(timezone.utc)
        ),
        route_distance_metres=3100,
        eta_seconds=420,
        route_geometry={
            "type": "LineString",
            "coordinates": [
                [28.2100, -25.7600],
                [28.2293, -25.7479],
            ],
        },
    )

    with patch(
        "app.api.controllers.alert."
        "get_property_route_handler",
        new=AsyncMock(return_value=data),
    ) as handler:
        response = await get_alert_property_route(
            property_id,
            db,
            claims,
        )

    assert response.status == 200
    assert response.data == data

    handler.assert_awaited_once_with(
        property_id=property_id,
        db=db,
        claims=claims
    )

@pytest.mark.asyncio
async def test_get_alert_tracking_timeline_delegates_to_service():
    alert_id = uuid4()
    db = MagicMock()
    claims = {"id": str(uuid4())}
    expected = TrackingTimelineResponse(
        status=200,
        message="ok",
        data=None,
    )

    with patch(
        "app.api.controllers.alert.get_tracking_timeline",
        new=AsyncMock(return_value=expected),
    ) as tracking_service:
        response = await get_alert_tracking_timeline(
            alert_id=alert_id,
            db=db,
            claims=claims,
        )

    assert response is expected
    tracking_service.assert_awaited_once_with(
        db=db,
        alert_id=alert_id,
        claims=claims,
    )
