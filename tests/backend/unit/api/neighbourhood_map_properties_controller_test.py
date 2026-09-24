from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.neighbourhood import (
    get_neighbourhood_map_properties,
)
from app.schemas.neighbourhood import (
    NeighbourhoodMapPropertyRes,
)


NEIGHBOURHOOD_ID = uuid4()
PROPERTY_ID = uuid4()
CLAIMS = {
    "id": str(uuid4()),
}


def make_property_response():
    return NeighbourhoodMapPropertyRes(
        id=PROPERTY_ID,
        address="12 Main Street",
        property_type="PRIVATE",
        latitude=-25.7479,
        longitude=28.2293,
    )


@pytest.mark.asyncio
async def test_delegates_to_map_properties_service():
    db = Mock()
    expected = [make_property_response()]

    with patch(
        "app.api.controllers.neighbourhood."
        "get_neighbourhood_map_properties_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_neighbourhood_map_properties(
            neighbourhood_id=NEIGHBOURHOOD_ID,
            db=db,
            claims=CLAIMS,
        )

    assert response is expected

    handler.assert_awaited_once_with(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        db=db,
        claims=CLAIMS,
    )


@pytest.mark.asyncio
async def test_propagates_service_authentication_error():
    db = Mock()
    error = HTTPException(
        status_code=401,
        detail="Not authenticated",
    )

    with patch(
        "app.api.controllers.neighbourhood."
        "get_neighbourhood_map_properties_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_neighbourhood_map_properties(
                neighbourhood_id=NEIGHBOURHOOD_ID,
                db=db,
                claims=None,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        db=db,
        claims=None,
    )