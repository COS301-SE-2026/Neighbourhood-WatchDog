from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.neighbourhood_service import (
    get_neighbourhood_map_properties_handler,
)


NEIGHBOURHOOD_ID = uuid4()
USER_ID = uuid4()


def make_property(
    *,
    address="12 Main Street",
    property_type="PRIVATE",
    latitude=-25.7479,
    longitude=28.2293,
):
    property_obj = Mock()
    property_obj.id = uuid4()
    property_obj.address = address
    property_obj.property_type = property_type
    property_obj.latitude = latitude
    property_obj.longitude = longitude
    property_obj.neighbourhood_id = NEIGHBOURHOOD_ID
    return property_obj


def make_db(properties):
    db = AsyncMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = properties

    db.execute.return_value = result
    return db


@pytest.mark.asyncio
async def test_requires_authentication():
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_neighbourhood_map_properties_handler(
            neighbourhood_id=NEIGHBOURHOOD_ID,
            db=db,
            claims=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_geocoded_and_ungeocoded_properties():
    geocoded = make_property(
        address="12 Main Street",
        latitude=-25.7479,
        longitude=28.2293,
    )

    ungeocoded = make_property(
        address="Unknown Location",
        property_type="PUBLIC",
        latitude=None,
        longitude=None,
    )

    db = make_db([geocoded, ungeocoded])

    result = await get_neighbourhood_map_properties_handler(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        db=db,
        claims={"id": str(USER_ID)},
    )

    assert len(result) == 2

    assert result[0].id == geocoded.id
    assert result[0].address == "12 Main Street"
    assert result[0].property_type == "PRIVATE"
    assert result[0].latitude == -25.7479
    assert result[0].longitude == 28.2293

    assert result[1].id == ungeocoded.id
    assert result[1].address == "Unknown Location"
    assert result[1].property_type == "PUBLIC"
    assert result[1].latitude is None
    assert result[1].longitude is None


@pytest.mark.asyncio
async def test_returns_empty_list_when_neighbourhood_has_no_properties():
    db = make_db([])

    result = await get_neighbourhood_map_properties_handler(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        db=db,
        claims={"id": str(USER_ID)},
    )

    assert result == []
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_queries_the_requested_neighbourhood():
    db = make_db([])

    await get_neighbourhood_map_properties_handler(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        db=db,
        claims={"id": str(USER_ID)},
    )

    statement = db.execute.await_args.args[0]
    statement_text = str(statement)

    assert "property.neighbourhood_id" in statement_text
    assert "ORDER BY property.address" in statement_text