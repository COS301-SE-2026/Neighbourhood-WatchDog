import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from typing import cast
import pytest
from fastapi import HTTPException

from app.services.neighbourhood_join_service import (
    request_to_join_handler,
    resolve_join_request_handler,
    list_join_requests_handler,
)
from app.models.neighbourhood import Neighbourhood
from app.models.neighbourhood_join_request import NeighbourhoodJoinRequest
from app.models.user import User

NEIGHBOURHOOD_PATCH = "app.services.neighbourhood_join_service.NeighbourhoodJoinRequest"
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
            NEIGHBOURHOOD_PATCH,
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
            NEIGHBOURHOOD_PATCH,
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

class TestListJoinRequests:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.mock_db.rollback = Mock()
 
        self.neighbourhood_id = uuid.uuid4()
        self.admin_claims = {
            "sub": "cognito-sub-admin",
            "custom:role": "NEIGHBOURHOOD_ADMIN",
            "custom:neighbourhood_id": str(self.neighbourhood_id),
        }
 
        self.join_request_patcher = patch(
            NEIGHBOURHOOD_PATCH,
            new=NeighbourhoodJoinRequest,
        )
        self.join_request_patcher.start()
 
    def teardown_method(self):
        self.join_request_patcher.stop()
 
    @pytest.mark.asyncio
    async def test_missing_db_raises_500(self):
        with pytest.raises(HTTPException) as exc:
            await list_join_requests_handler(cast(Mock, None), self.admin_claims)
 
        assert exc.value.status_code == 500
 
    @pytest.mark.asyncio
    async def test_missing_claims_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            await list_join_requests_handler(self.mock_db, cast(dict, None))
 
        assert exc.value.status_code == 401
 
    @pytest.mark.asyncio
    async def test_non_admin_role_raises_403(self):
        claims = {**self.admin_claims, "custom:role": "RESIDENT"}
 
        with pytest.raises(HTTPException) as exc:
            await list_join_requests_handler(self.mock_db, claims)
 
        assert exc.value.status_code == 403
        assert exc.value.detail == "Insufficient permissions"
 
    @pytest.mark.asyncio
    async def test_missing_neighbourhood_id_raises_403(self):
        claims = {**self.admin_claims}
        del claims["custom:neighbourhood_id"]
 
        with pytest.raises(HTTPException) as exc:
            await list_join_requests_handler(self.mock_db, claims)
 
        assert exc.value.status_code == 403
        assert exc.value.detail == "Neighbourhood context missing"
 
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_requests(self):
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = []
 
        result = await list_join_requests_handler(self.mock_db, self.admin_claims)
 
        assert result == []
 
    @pytest.mark.asyncio
    async def test_returns_pending_requests_for_admin_neighbourhood(self):
        request_1 = Mock()
        request_1.id = uuid.uuid4()
        request_1.neighbourhood_id = self.neighbourhood_id
        request_1.user_id = uuid.uuid4()
        request_1.status = "PENDING"
        request_1.created_at = datetime.now(timezone.utc)
 
        request_2 = Mock()
        request_2.id = uuid.uuid4()
        request_2.neighbourhood_id = self.neighbourhood_id
        request_2.user_id = uuid.uuid4()
        request_2.status = "PENDING"
        request_2.created_at = datetime.now(timezone.utc)
 
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = [
            request_1,
            request_2,
        ]
 
        result = await list_join_requests_handler(self.mock_db, self.admin_claims)
 
        assert len(result) == 2
        assert result[0].neighbourhood_id == self.neighbourhood_id
        assert result[1].neighbourhood_id == self.neighbourhood_id
