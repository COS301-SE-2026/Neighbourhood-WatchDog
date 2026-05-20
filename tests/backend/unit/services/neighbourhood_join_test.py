import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.services.neighbourhood_join_service import (
    request_to_join_handler,
    resolve_join_request_handler,
)
from app.models.neighbourhood import Neighbourhood
from app.models.neighbourhood_join_request import NeighbourhoodJoinRequest
from app.models.user import User


class TestRequestToJoin:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()
        self.claims = {"sub": "cognito-sub-123", "custom:role": "RESIDENT"}

        self._added = []

        def _ensure_defaults(obj):
            if hasattr(obj, "id") and getattr(obj, "id") is None:
                obj.id = uuid.uuid4()
            if hasattr(obj, "created_at") and getattr(obj, "created_at") is None:
                obj.created_at = datetime.now(timezone.utc)

        def _add(obj):
            self._added.append(obj)

        def _flush():
            if self._added:
                _ensure_defaults(self._added[-1])

        def _refresh(obj):
            _ensure_defaults(obj)

        self.mock_db.add.side_effect = _add
        self.mock_db.flush.side_effect = _flush
        self.mock_db.refresh.side_effect = _refresh

        self.neighbourhood_patcher = patch(
            "app.services.neighbourhood_join_service.Neighbourhood",
            new=Neighbourhood,
        )
        self.join_request_patcher = patch(
            "app.services.neighbourhood_join_service.NeighbourhoodJoinRequest",
            new=NeighbourhoodJoinRequest,
        )
        self.user_patcher = patch(
            "app.services.neighbourhood_join_service.User",
            new=User,
        )

        self.neighbourhood_patcher.start()
        self.join_request_patcher.start()
        self.user_patcher.start()

    def teardown_method(self):
        self.neighbourhood_patcher.stop()
        self.join_request_patcher.stop()
        self.user_patcher.stop()

    @pytest.mark.asyncio
    async def test_missing_join_code_raises_400(self):
        with pytest.raises(HTTPException) as exc:
            await request_to_join_handler("", self.mock_db, self.claims)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_db_raises_500(self):
        with pytest.raises(HTTPException) as exc:
            await request_to_join_handler("abcd", None, self.claims)

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_missing_claims_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            await request_to_join_handler("abcd", self.mock_db, None)

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_join_code_raises_404(self):
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [None]

        with pytest.raises(HTTPException) as exc:
            await request_to_join_handler("badcode", self.mock_db, self.claims)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Invalid join code"

    @pytest.mark.asyncio
    async def test_user_not_found_raises_401(self):
        neighbourhood = Mock()
        neighbourhood.id = uuid.uuid4()
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            neighbourhood,
            None,
        ]

        with pytest.raises(HTTPException) as exc:
            await request_to_join_handler("abcd", self.mock_db, self.claims)

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_pending_request_raises_409(self):
        neighbourhood = Mock()
        neighbourhood.id = uuid.uuid4()
        user = Mock()
        user.id = uuid.uuid4()
        pending = Mock()

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            neighbourhood,
            user,
            pending,
        ]

        with pytest.raises(HTTPException) as exc:
            await request_to_join_handler("abcd", self.mock_db, self.claims)

        assert exc.value.status_code == 409
        assert exc.value.detail == "Already have a pending request"

    @pytest.mark.asyncio
    async def test_happy_path_creates_request(self):
        neighbourhood = Mock()
        neighbourhood.id = uuid.uuid4()
        user = Mock()
        user.id = uuid.uuid4()

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            neighbourhood,
            user,
            None,
        ]

        result = await request_to_join_handler("abcd", self.mock_db, self.claims)

        assert result.neighbourhood_id == neighbourhood.id
        assert result.user_id == user.id
        assert result.status == "PENDING"
        assert self.mock_db.add.call_count == 1
        assert self.mock_db.flush.call_count == 1
        assert self.mock_db.commit.call_count == 1


class TestResolveJoinRequest:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()
        self.admin_claims = {
            "sub": "cognito-sub-123",
            "custom:role": "NEIGHBOURHOOD_ADMIN",
        }

        self.join_request_patcher = patch(
            "app.services.neighbourhood_join_service.NeighbourhoodJoinRequest",
            new=NeighbourhoodJoinRequest,
        )
        self.user_patcher = patch(
            "app.services.neighbourhood_join_service.User",
            new=User,
        )

        self.join_request_patcher.start()
        self.user_patcher.start()

    def teardown_method(self):
        self.join_request_patcher.stop()
        self.user_patcher.stop()

    @pytest.mark.asyncio
    async def test_missing_request_id_raises_400(self):
        with pytest.raises(HTTPException) as exc:
            await resolve_join_request_handler(None, "APPROVE", self.mock_db, self.admin_claims)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_db_raises_500(self):
        with pytest.raises(HTTPException) as exc:
            await resolve_join_request_handler(uuid.uuid4(), "APPROVE", None, self.admin_claims)

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_missing_claims_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            await resolve_join_request_handler(uuid.uuid4(), "APPROVE", self.mock_db, None)

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_request_not_found_raises_404(self):
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [None]

        with pytest.raises(HTTPException) as exc:
            await resolve_join_request_handler(uuid.uuid4(), "APPROVE", self.mock_db, self.admin_claims)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_wrong_role_raises_403(self):
        join_request = Mock()
        join_request.status = "PENDING"
        join_request.user_id = uuid.uuid4()

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            join_request,
        ]

        claims = {"sub": "cognito-sub-123", "custom:role": "RESIDENT"}
        with pytest.raises(HTTPException) as exc:
            await resolve_join_request_handler(uuid.uuid4(), "APPROVE", self.mock_db, claims)

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_already_resolved_raises_409(self):
        join_request = Mock()
        join_request.status = "APPROVED"
        join_request.user_id = uuid.uuid4()

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            join_request,
        ]

        with pytest.raises(HTTPException) as exc:
            await resolve_join_request_handler(uuid.uuid4(), "DENY", self.mock_db, self.admin_claims)

        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_user_not_found_raises_404(self):
        join_request = Mock()
        join_request.status = "PENDING"
        join_request.user_id = uuid.uuid4()

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            join_request,
            None,
        ]

        with pytest.raises(HTTPException) as exc:
            await resolve_join_request_handler(uuid.uuid4(), "APPROVE", self.mock_db, self.admin_claims)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_approve_sets_role_and_neighbourhood(self):
        join_request = Mock()
        join_request.id = uuid.uuid4()
        join_request.status = "PENDING"
        join_request.user_id = uuid.uuid4()
        join_request.neighbourhood_id = uuid.uuid4()
        join_request.created_at = datetime.now(timezone.utc)

        user = Mock()
        user.role = "RESIDENT"
        user.neighbourhood_id = None

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            join_request,
            user,
        ]

        result = await resolve_join_request_handler(uuid.uuid4(), "APPROVE", self.mock_db, self.admin_claims)

        assert result.status == "APPROVED"
        assert user.neighbourhood_id == join_request.neighbourhood_id
        assert user.role == "RESIDENT"
        assert self.mock_db.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_deny_sets_denied_status(self):
        join_request = Mock()
        join_request.id = uuid.uuid4()
        join_request.status = "PENDING"
        join_request.user_id = uuid.uuid4()
        join_request.neighbourhood_id = uuid.uuid4()
        join_request.created_at = datetime.now(timezone.utc)

        user = Mock()
        user.role = "RESIDENT"

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            join_request,
            user,
        ]

        result = await resolve_join_request_handler(uuid.uuid4(), "DENY", self.mock_db, self.admin_claims)

        assert result.status == "DENIED"
        assert self.mock_db.commit.call_count == 1
