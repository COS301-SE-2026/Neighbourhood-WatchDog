from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.alert import (
    AlertDistanceData,
    RouteGeometry,
)
from app.services.alert_route_service import (
    RoutingServiceUnavailable,
    calculate_property_distance_handler,
    get_property_route_handler,
)


NOW = datetime.now(timezone.utc)
PROPERTY_ID = uuid4()
CLAIMS = {"sub": "officer-cognito-sub"}


def make_distance() -> AlertDistanceData:
    return AlertDistanceData(
        property_id=PROPERTY_ID,
        property_address="123 Test Street, Pretoria",
        property_latitude=-25.7479,
        property_longitude=28.2293,
        officer_latitude=-25.7600,
        officer_longitude=28.2100,
        distance_metres=2500,
        officer_location_updated_at=NOW,
    )


def make_db_row():
    return SimpleNamespace(
        property_id=PROPERTY_ID,
        property_address="123 Test Street, Pretoria",
        property_latitude=-25.7479,
        property_longitude=28.2293,
        officer_latitude=-25.7600,
        officer_longitude=28.2100,
        distance_metres=2500,
        has_officer_location=True,
        officer_location_updated_at=NOW,
    )


def make_db(row):
    result = MagicMock()
    result.one_or_none.return_value = row

    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    return db


class TestPropertyDistance:
    @pytest.mark.asyncio
    async def test_returns_distance_for_valid_locations(
        self,
    ):
        db = make_db(make_db_row())

        with patch(
            "app.services.alert_route_service."
            "is_location_stale",
            return_value=False,
        ):
            result = (
                await calculate_property_distance_handler(
                    property_id=PROPERTY_ID,
                    db=db,
                    claims=CLAIMS,
                )
            )

        assert result.property_id == PROPERTY_ID
        assert result.distance_metres == 2500
        assert result.officer_latitude == -25.7600
        assert result.property_latitude == -25.7479
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_missing_authentication(self):
        db = MagicMock()
        db.execute = AsyncMock()

        with pytest.raises(
            HTTPException
        ) as exc_info:
            await calculate_property_distance_handler(
                property_id=PROPERTY_ID,
                db=db,
                claims={},
            )

        assert exc_info.value.status_code == 401
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rejects_property_outside_officer_neighbourhood(
        self,
    ):
        db = make_db(None)

        with pytest.raises(
            HTTPException
        ) as exc_info:
            await calculate_property_distance_handler(
                property_id=PROPERTY_ID,
                db=db,
                claims=CLAIMS,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_rejects_stale_officer_location(
        self,
    ):
        db = make_db(make_db_row())

        with patch(
            "app.services.alert_route_service."
            "is_location_stale",
            return_value=True,
        ):
            with pytest.raises(
                HTTPException
            ) as exc_info:
                await calculate_property_distance_handler(
                    property_id=PROPERTY_ID,
                    db=db,
                    claims=CLAIMS,
                )

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail == (
            "Officer location is stale"
        )
