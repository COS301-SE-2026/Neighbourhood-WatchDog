import json
from unittest.mock import AsyncMock, Mock

import pytest

from app.core import cache


@pytest.mark.asyncio
async def test_get_redis_creates_and_reuses_client(monkeypatch):
    redis_client = Mock()
    from_url = Mock(return_value=redis_client)

    monkeypatch.setattr(
        cache.redis,
        "from_url",
        from_url,
    )

    cache._redis_client = None

    first = cache.get_redis()
    second = cache.get_redis()

    assert first is redis_client
    assert second is redis_client
    from_url.assert_called_once()


@pytest.mark.asyncio
async def test_cache_get_or_set_fetches_on_cache_miss(monkeypatch):
    redis_client = AsyncMock()
    redis_client.get.return_value = None

    monkeypatch.setattr(
        cache,
        "get_redis",
        lambda: redis_client,
    )

    fetch_fn = AsyncMock(
        return_value={"status": "fresh"},
    )

    result = await cache.cache_get_or_set(
        "camera:1",
        60,
        fetch_fn,
    )

    assert result == {"status": "fresh"}
    fetch_fn.assert_awaited_once()
    redis_client.setex.assert_awaited_once_with(
        "camera:1",
        60,
        json.dumps({"status": "fresh"}),
    )


@pytest.mark.asyncio
async def test_cache_invalidate_deletes_keys(monkeypatch):
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
async def test_cache_invalidate_prefix_scans_and_deletes(
    monkeypatch,
):
    redis_client = AsyncMock()

    async def scan_iter(match):
        assert match == "camera:*"
        yield "camera:1"
        yield "camera:2"

    redis_client.scan_iter = scan_iter

    monkeypatch.setattr(
        cache,
        "get_redis",
        lambda: redis_client,
    )

    await cache.cache_invalidate_prefix("camera:")

    assert redis_client.delete.await_count == 2
    redis_client.delete.assert_any_await("camera:1")
    redis_client.delete.assert_any_await("camera:2")