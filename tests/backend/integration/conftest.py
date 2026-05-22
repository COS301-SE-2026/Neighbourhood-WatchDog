import os

os.environ["SKIP_DB_INIT"] = "false"

postgres_user = os.getenv("POSTGRES_USER", "postgres")
postgres_password = os.getenv("POSTGRES_PASSWORD", "postgres")
postgres_db = os.getenv("POSTGRES_DB", "watchdog")
os.environ["DATABASE_URL"] = (
    f"postgresql://{postgres_user}:{postgres_password}@localhost:5432/{postgres_db}"
)

import pytest
from httpx import AsyncClient
try:
    # ASGITransport may be in different places depending on httpx version
    from httpx import ASGITransport 
except Exception:
    try:
        from httpx._transports.asgi import ASGITransport  
    except Exception:
        ASGITransport = None 
import main as main_module


@pytest.fixture
async def async_client():
    """Async HTTP client bound to the FastAPI app."""
    # AsyncClient supports creating with `app=` in newer httpx versions.
    # If that fails, fall back to creating an ASGITransport instance.
    try:
        async with AsyncClient(app=main_module.app, base_url="http://testserver") as ac:
            yield ac
    except TypeError:
        if ASGITransport is None:
            raise
        transport = ASGITransport(app=main_module.app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac


@pytest.fixture
def auth_headers():
    return {
        "Authorization": "Bearer test",
        "X-Mock-Role": "RESIDENT",
        "X-Mock-Sub": "00000000-0000-0000-0000-000000000001",
    }


@pytest.fixture
def admin_headers():
    return {
        "Authorization": "Bearer test",
        "X-Mock-Role": "NEIGHBOURHOOD_ADMIN",
        "X-Mock-Sub": "11111111-1111-1111-1111-111111111111",
    }


@pytest.fixture
def internal_headers():
    return {
        "X-Internal-Token": "dev-token",
        "Authorization": "Bearer test",
    }
