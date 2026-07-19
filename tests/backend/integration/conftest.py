import os
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

TEST_BEARER = "Bearer test"

def pytest_configure(config):
    os.environ["TESTING"] = "true"
    os.environ["SKIP_DB_INIT"] = "false"
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_db = os.getenv("POSTGRES_DB", "watchdog")
    os.environ["DATABASE_URL"] = f"postgresql://{postgres_user}:{postgres_password}@localhost:5432/{postgres_db}"

def _get_main_module():
    import main as main_module
    return main_module

@pytest.fixture
async def async_client():
    """Async HTTP client bound to the FastAPI app."""
    # AsyncClient supports creating with `app=` in newer httpx versions.
    # If that fails, fall back to creating an ASGITransport instance.
    main_module = _get_main_module()
    try:
        async with AsyncClient(app=main_module.app, base_url="https://testserver") as ac:
            yield ac
    except TypeError:
        if ASGITransport is None:
            raise
        transport = ASGITransport(app=main_module.app)
        async with AsyncClient(transport=transport, base_url="https://testserver") as ac:
            yield ac


@pytest.fixture
def auth_headers():
    return {
        "Authorization": TEST_BEARER,
        "X-Mock-Role": "RESIDENT",
        "X-Mock-Sub": "a16cd2b8-c0c1-70f7-1fb6-17b5cea57bcf",
    }


@pytest.fixture
def admin_headers():
    return {
        "Authorization": TEST_BEARER,
        "X-Mock-Role": "NEIGHBOURHOOD_ADMIN",
        "X-Mock-Sub": "a16cd2b8-c0c1-70f7-1fb6-17b5cea57bcf",
    }


@pytest.fixture
def internal_headers():
    return {
        "X-Internal-Token": "dev-token",
        "Authorization": TEST_BEARER,
    }

@pytest.fixture
def pending_user_headers():
    return{
        "Authorization": TEST_BEARER,
        "X-Mock-Role": "RESIDENT",
        "X-Mock-Sub": "22222222-2222-2222-2222-222222222222",
        "X-Mock-Neighbourhood-Id": "",
    }