from fastapi.routing import APIRoute, APIWebSocketRoute

from app.auth.dependencies import get_authenticated_edge_agent, get_current_user
from app.auth.middleware import is_public_path
from main import app

AUTH_DEPENDENCIES = {get_current_user, get_authenticated_edge_agent}

SELF_AUTHENTICATING_WEBSOCKETS = {
    "/alerts/{neighbourhood_id}/ws",
    "/api/stream/cameras/{camera_id}/annotations/ws",
}

def _has_auth_dependency(dependant) -> bool:
    for dep in dependant.dependencies:
        if dep.call in AUTH_DEPENDENCIES or _has_auth_dependency(dep):
            return True

    return False

def test_every_route_requires_auth_or_is_explicity_public():
    """This test goes through all the routes in the backend and makes
    sure that the ones that should be public are public and the rest are not"""

    unprotected = []

    for route in app.routes:
        if isinstance(route, APIWebSocketRoute):
        
            if route.path not in SELF_AUTHENTICATING_WEBSOCKETS:
                unprotected.append(f"WS {route.path}")
        
        elif isinstance(route, APIRoute):
            if not _has_auth_dependency(route.dependant) and not is_public_path(route.path):
                unprotected.append(f"{sorted(route.methods)} {route.path}")

    assert not unprotected, "Route with no auth and not on the public allowlist:\n" + "\n".join(unprotected)