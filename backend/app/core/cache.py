import json
import os
from typing import Any, Callable, Awaitable

import redis.asyncio as redis

_redis_client: redis.Redis | None = None

def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    return _redis_client

async def cache_get_or_set(
    key: str,
    ttl_seconds: int,
    fetch_fn: Callable[[], Awaitable[Any]]
) -> Any:
    r = get_redis()
    cached = await r.get(key)
    if cached is not None:
        return json.loads(cached)

    result = await fetch_fn()
    await r.setex(key, ttl_seconds, json.dumps(result))
    return result

async def cache_invalidate(*keys: str) -> None:
    if not keys:
        return
    r = get_redis()
    await r.delete(*keys)

async def cache_invalidate_prefix(prefix: str) -> None:
    r = get_redis()
    async for key in r.scan_iter(match=f"{prefix}*"):
        await r.delete(key)