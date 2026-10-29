import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from app.auth import jwt as auth_jwt
from app.auth.middleware import AuthMiddleware


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


@pytest.fixture
def protected_client(monkeypatch, signing_key):
    # The normal test configuration bypasses authentication.
    # Disable that bypass so these tests exercise real verification.
    monkeypatch.setenv("TESTING", "false")

    public_jwk = json.loads(
        RSAAlgorithm.to_jwk(signing_key.public_key())
    )
    public_jwk["kid"] = "test-signing-key"

    # Use our test key instead of requesting Cognito's keys.
    monkeypatch.setattr(
        auth_jwt,
        "get_jwks",
        lambda: [public_jwk],
    )

    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/protected")
    def protected():
        return {"status": "ok"}

    with TestClient(app) as client:
        yield client


def make_token(signing_key, overrides=None, remove=None):
    now = int(time.time())
    claims = {
        "sub": "test-user",
        "iss": auth_jwt.ISSUER,
        "iat": now,
        "exp": now + 300,
        "token_use": "access",
        "client_id": auth_jwt.config.cognito_client_id,
    }
    claims.update(overrides or {})

    for name in remove or []:
        claims.pop(name, None)

    return jwt.encode(
        claims,
        signing_key,
        algorithm="RS256",
        headers={"kid": "test-signing-key"},
    )


def test_valid_access_token_returns_200(protected_client, signing_key):
    token = make_token(signing_key)

    response = protected_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "overrides",
    [
        {"client_id": "another-client"},
        # Retain the correct client_id to isolate token_use validation.
        {"token_use": "id"},
        {"iss": "https://example.invalid/another-pool"},
        {"exp": int(time.time()) - 300},
    ],
    ids=["wrong-client", "id-token", "wrong-issuer", "expired"],
)
def test_invalid_claims_return_401(
    protected_client, signing_key, overrides
):
    token = make_token(signing_key, overrides=overrides)

    response = protected_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "claim",
    ["exp", "iss", "sub", "token_use", "client_id"],
)
def test_missing_required_claim_returns_401(
    protected_client, signing_key, claim
):
    token = make_token(signing_key, remove=[claim])

    response = protected_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_realistic_id_token_returns_401(protected_client, signing_key):
    token = make_token(
        signing_key,
        overrides={
            "token_use": "id",
            "aud": auth_jwt.config.cognito_client_id,
        },
        remove=["client_id"],
    )

    response = protected_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401