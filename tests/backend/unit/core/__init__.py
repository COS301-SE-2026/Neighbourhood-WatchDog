import json
from unittest.mock import AsyncMock

import pytest

from app.core import cache


@pytest.mark.asyncio
async def test_cache_get_or_set_returns_cached_value(monkeypatch):
    redis_client = AsyncMock()
    redis_client.get.return_value = json.dumps(
        {"name": "cached"},
    )

    monkeypatch.setattr(
        cache,
        "get_redis",
        lambda: redis_client,
    )

    fetch_fn = AsyncMock()

    result = await cache.cache_get_or_set(
        "camera:1",
        60,
        fetch_fn,
    )

    assert result == {"name": "cached"}
    fetch_fn.assert_not_awaited()
    redis_client.setex.assert_not_awaited()


@pytest.mark.asyncio
async def test_cache_get_or_set_fetches_and_stores_on_cache_miss(
    monkeypatch,
):
    redis_client = AsyncMock()
    redis_client.get.return_value = None

    monkeypatch.setattr(
        cache,
        "get_redis",
        lambda: redis_client,
    )

    fetch_fn = AsyncMock(
        return_value={"name": "fresh"},
    )

    result = await cache.cache_get_or_set(
        "camera:1",
        60,
        fetch_fn,
    )

    assert result == {"name": "fresh"}
    fetch_fn.assert_awaited_once()
    redis_client.setex.assert_awaited_once_with(
        "camera:1",
        60,
        json.dumps({"name": "fresh"}),
    )


@pytest.mark.asyncio
async def test_cache_invalidate_does_nothing_without_keys(
    monkeypatch,
):
    get_redis = AsyncMock()

    monkeypatch.setattr(
        cache,
        "get_redis",
        get_redis,
    )

    await cache.cache_invalidate()

    get_redis.assert_not_awaited()


@pytest.mark.asyncio
async def test_cache_invalidate_deletes_all_keys(monkeypatch):
    redis_client = AsyncMock()

    monkeypatch.setattr(
        cache,
        "get_redis",
        lambda: redis_client,
    )

    await cache.cache_invalidate(
        "camera:1",
        "camera:2",
    )

    redis_client.delete.assert_awaited_once_with(
        "camera:1",
        "camera:2",
    )


@pytest.mark.asyncio
async def test_cache_invalidate_prefix_deletes_matching_keys(
    monkeypatch,
):
    redis_client = AsyncMock()

    async def scan_iter(match):
        assert match == "camera:*"

        for key in ("camera:1", "camera:2"):
            yield key

    redis_client.scan_iter = scan_iter

    monkeypatch.setattr(
        cache,
        "get_redis",
        lambda: redis_client,
    )

    await cache.cache_invalidate_prefix("camera:")

    assert redis_client.delete.await_count == 2