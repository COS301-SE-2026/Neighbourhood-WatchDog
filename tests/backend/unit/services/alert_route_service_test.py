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
