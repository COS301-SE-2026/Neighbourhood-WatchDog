from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.camera_coverage_calculation_service import (
    load_neighbourhood_camera_coverages,
)


@pytest.mark.asyncio
async def test_loads_enabled_camera_coverage_for_neighbourhood():
    row = {
        "enabled": True,
        "property_latitude": -25.747,
        "property_longitude": 28.229,
        "origin_latitude": -25.747,
        "origin_longitude": 28.229,
        "coverage_bearing_degrees": 90.0,
        "coverage_angle_degrees": 60.0,
        "coverage_range_metres": 100.0,
    }

    mappings = MagicMock()
    mappings.all.return_value = [row]

    query_result = MagicMock()
    query_result.mappings.return_value = mappings

    db = MagicMock()
    db.execute = AsyncMock(
        return_value=query_result
    )

    result = await load_neighbourhood_camera_coverages(
        neighbourhood_id=uuid4(),
        db=db,
    )

    assert len(result) == 1
    assert result[0].enabled is True
    assert result[0].property_latitude == -25.747
    assert result[0].property_longitude == 28.229
    assert result[0].coverage_bearing_degrees == 90.0
    assert result[0].coverage_angle_degrees == 60.0
    assert result[0].coverage_range_metres == 100.0

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_empty_list_without_configured_cameras():
    mappings = MagicMock()
    mappings.all.return_value = []

    query_result = MagicMock()
    query_result.mappings.return_value = mappings

    db = MagicMock()
    db.execute = AsyncMock(
        return_value=query_result
    )

    result = await load_neighbourhood_camera_coverages(
        neighbourhood_id=uuid4(),
        db=db,
    )

    assert result == []
