import jwt
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from starlette.requests import Request

from app.auth import jwt as jwt_module


def make_request(headers=None):
    headers = headers or {}
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/private",
        "headers": [
            (key.lower().encode(), value.encode())
            for key, value in headers.items()
        ],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("testclient", 50000),
        "scheme": "http",
    }
    return Request(scope)


def test_get_authenticated_claims_rejects_missing_authorization_header():
    request = make_request()

    with patch.dict("os.environ", {"TESTING": "false"}):
        with pytest.raises(HTTPException) as exc_info:
            jwt_module.get_authenticated_claims(request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing Authorization header"


def test_get_authenticated_claims_rejects_non_bearer_header():
    request = make_request(
        {"Authorization": "Basic abc123"}
    )

    with patch.dict("os.environ", {"TESTING": "false"}):
        with pytest.raises(HTTPException) as exc_info:
            jwt_module.get_authenticated_claims(request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid Authorization header"


def test_get_authenticated_claims_returns_cached_request_claims():
    request = make_request()
    request.state.claims = {"sub": "cached-user"}

    result = jwt_module.get_authenticated_claims(request)

    assert result == {"sub": "cached-user"}


def test_get_authenticated_claims_stores_verified_claims():
    request = make_request(
        {"Authorization": "Bearer valid-token"}
    )
    claims = {"sub": "verified-user"}

    with patch.dict("os.environ", {"TESTING": "false"}):
        with patch(
            "app.auth.jwt.verify_jwt",
            return_value=claims,
        ):
            result = jwt_module.get_authenticated_claims(request)

    assert result == claims
    assert request.state.claims == claims


def test_get_authenticated_claims_converts_jwt_error_to_401():
    request = make_request(
        {"Authorization": "Bearer invalid-token"}
    )

    with patch.dict("os.environ", {"TESTING": "false"}):
        with patch(
            "app.auth.jwt.verify_jwt",
            side_effect=jwt.PyJWTError("invalid token"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                jwt_module.get_authenticated_claims(request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token"