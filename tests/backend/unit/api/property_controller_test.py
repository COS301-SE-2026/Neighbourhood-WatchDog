from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.api.controllers.property import (
    create_property,
    get_property_details,
    get_user_properties,
)
from app.models.property import PropertyTypeEnum
from app.schemas.property import CreatePropertyReq


PROPERTY_ID = uuid4()
CLAIMS = {"sub": "cognito-sub-123"}
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_property():
    return SimpleNamespace(
        id=PROPERTY_ID,
        neighbourhood_id=None,
        address="123 Test Street",
        property_type=PropertyTypeEnum.PRIVATE,
        latitude=-26.2041,
        longitude=28.0473,
        created_at=CREATED_AT,
    )


@pytest.mark.asyncio
async def test_create_property_maps_coordinates_and_delegates():
    db = Mock()
    request = CreatePropertyReq(
        address="123 Test Street",
        property_type=PropertyTypeEnum.PRIVATE,
        latitude=-26.2041,
        longitude=28.0473,
    )
    created_property = make_property()

    with patch(
        "app.api.controllers.property.create_property_handler",
        new=AsyncMock(return_value=created_property),
    ) as handler:
        response = await create_property(request, db, CLAIMS)

    assert response.status == 201
    assert response.message == "Property Created Successfully"
    assert response.data.property_id == PROPERTY_ID
    assert response.data.latitude == -26.2041
    assert response.data.longitude == 28.0473
    handler.assert_awaited_once_with(
        request.address,
        request.property_type,
        CLAIMS,
        db,
        latitude=request.latitude,
        longitude=request.longitude,
    )


@pytest.mark.asyncio
async def test_get_user_properties_maps_all_property_fields():
    db = Mock()
    property_obj = make_property()

    with patch(
        "app.api.controllers.property.get_user_properties_handler",
        new=AsyncMock(return_value=[property_obj]),
    ) as handler:
        response = await get_user_properties(db, CLAIMS)

    assert len(response) == 1
    assert response[0].property_id == PROPERTY_ID
    assert response[0].address == "123 Test Street"
    assert response[0].latitude == -26.2041
    assert response[0].longitude == 28.0473
    handler.assert_awaited_once_with(CLAIMS, db)


@pytest.mark.asyncio
async def test_get_property_details_delegates_to_service():
    db = Mock()
    expected = {"property_id": PROPERTY_ID, "address": "123 Test Street"}

    with patch(
        "app.api.controllers.property.get_property_details_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_property_details(PROPERTY_ID, db, CLAIMS)

    assert response == expected
    handler.assert_awaited_once_with(PROPERTY_ID, db, CLAIMS)
