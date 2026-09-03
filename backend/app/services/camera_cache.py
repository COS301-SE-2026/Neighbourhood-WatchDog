from uuid import UUID

from app.core.cache import cache_invalidate

def _norm(
    property_id: str | UUID
) -> str:
    """Canonicalise a prop id so a path stirng and uuid map to the same key"""
    try:
        return str(UUID(str(property_id)))
    except(ValueError, AttributeError, TypeError):
        return str(property_id)

def camera_property_cache_key(
    property_id: str | UUID
) -> str:
    """Resident or admin camera list for a property """
    return f"cache:camera:property:{_norm(property_id)}"

def camera_internal_cache_key(
    property_id: str | UUID
) -> str:
    """Resident or admin camera list for a property """
    return f"cache:camera:internal:property_id:{_norm(property_id)}"

async def invalidate_camera_caches(property_id: str | UUID) -> None:
    """Bust both camera list caches for a property
        Call after committing any change to a camera row, its confidence
        threshold, or its detection zones."""

    await cache_invalidate(
        camera_property_cache_key(property_id),
        camera_internal_cache_key(property_id),
    )