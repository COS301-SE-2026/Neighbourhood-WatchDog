from unittest.mock import AsyncMock

import pytest

from app.services import camera_cache


def test_property_cache_key_normalizes_uuid():
    property_id = "40000000-0000-0000-0000-000000000001"

    assert camera_cache.camera_property_cache_key(property_id) == (
        "cache:camera:property:"
        "40000000-0000-0000-0000-000000000001"
    )


def test_internal_cache_key_normalizes_uuid():
    property_id = "40000000-0000-0000-0000-000000000001"

    assert camera_cache.camera_internal_cache_key(property_id) == (
        "cache:camera:internal:property_id:"
        "40000000-0000-0000-0000-000000000001"
    )


def test_invalid_property_id_is_preserved():
    assert camera_cache.camera_property_cache_key(
        "not-a-uuid",
    ) == "cache:camera:property:not-a-uuid"


@pytest.mark.asyncio
async def test_invalidate_camera_caches_invalidates_both_keys(
    monkeypatch,
):
    invalidate = AsyncMock()

    monkeypatch.setattr(
        camera_cache,
        "cache_invalidate",
        invalidate,
    )

    property_id = "40000000-0000-0000-0000-000000000001"

    await camera_cache.invalidate_camera_caches(property_id)

    invalidate.assert_awaited_once_with(
        camera_cache.camera_property_cache_key(property_id),
        camera_cache.camera_internal_cache_key(property_id),
    )