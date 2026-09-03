
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.models.property import PropertyTypeEnum
from app.services.alert_service import _build_alert_res
from app.services.property_service import create_property_handler


def make_alert(property_obj):

    camera = SimpleNamespace(property=property_obj)

    return SimpleNamespace(
        id=uuid4(),
        camera_id=uuid4(),
        camera=camera,
        frame_timestamp=datetime.now(timezone.utc),
        detection_type="HUMAN_PRESENCE",
        confidence_score=0.8,
        thumbnail_url=None,
        clip_s3_key=None,
        clip_expires_at=None,
        processed=True,
        status="OPEN",
        resolved_by=None,
        resolved_at=None,
        created_at=datetime.now(timezone.utc)
    )


def test_alert_response_includes_property_address_and_coordinates():

    property_obj = SimpleNamespace(
        address="12 Main Road, Cape Town",
        latitude=-33.9249,
        longitude=18.4241
    )

    response = _build_alert_res(make_alert(property_obj))

    assert response.property_address == "12 Main Road, Cape Town"
    assert response.property_latitude == -33.9249
    assert response.property_longitude == 18.4241


def test_alert_response_keeps_address_when_coordinates_are_missing():
    property_obj = SimpleNamespace(
        address="12 Main Road, Cape Town",
        latitude=None,
        longitude=None 
    )


    response = _build_alert_res(make_alert(property_obj))

    assert response.property_address == "12 Main Road, Cape Town"
    assert response.property_latitude is None
    assert response.property_longitude is None


@pytest.mark.asyncio
async def test_property_creation_persists_picker_coordinates():

    db = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = SimpleNamespace(id=uuid4())
    db.execute = AsyncMock(return_value=result)
    db.add = Mock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    claims = {"sub": "cognito-sub"}

    with patch("app.services.property_service.Property") as property_factory:
        property_obj = Mock()
        property_obj.id = uuid4()
        property_obj.property_type = PropertyTypeEnum.PRIVATE
        property_obj.neighbourhood_id = None
        property_factory.return_value = property_obj

        await create_property_handler(
            "12 Main Road, Cape Town",
            PropertyTypeEnum.PRIVATE,
            claims,
            db,
            latitude=-33.9249,
            longitude=18.4241

        )

        property_factory.assert_called_once_with(
            address="12 Main Road, Cape Town",
            latitude=-33.9249,
            longitude=18.4241,
            property_type=PropertyTypeEnum.PRIVATE

            
        )