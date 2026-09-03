
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.neighbourhood_join_request import JoinRequestStatus
from app.models.neighbourhood_user import NeighbourhoodRole
from app.services import neighbourhood_join_service as service


PROPERTY_ID = uuid.uuid4()
NEIGHBOURHOOD_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
REQUEST_ID = uuid.uuid4()


def result(*, scalar=None, rows=(), first=None):
    value = Mock()
    value.scalar_one_or_none.return_value = scalar
    value.scalars.return_value.all.return_value = list(rows)
    value.first.return_value = first
    return value


def make_db(results=()):
    db = Mock()
    db.execute = AsyncMock(side_effect=list(results))
    db.add = Mock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


def claims(user_id=USER_ID):
    return {"id": str(user_id), "sub": "cognito-sub", "custom:role": "RESIDENT"}


def make_request(status=JoinRequestStatus.PENDING):
    return SimpleNamespace(
        id=REQUEST_ID,
        neighbourhood_id=NEIGHBOURHOOD_ID,
        property_id=PROPERTY_ID,
        user_id=USER_ID,
        status=status,
        created_at=datetime.now(timezone.utc),
        resolved_at=None,
    )


class TestRequestToJoinAdditional:
    @pytest.mark.asyncio
    async def test_missing_db_is_rejected(self):
        with pytest.raises(HTTPException) as exc:
            await service.request_to_join_handler(PROPERTY_ID, "ABC123", None, claims())
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_blank_join_code_is_rejected(self):
        db = make_db()
        with pytest.raises(HTTPException) as exc:
            await service.request_to_join_handler(PROPERTY_ID, "  ", db, claims())
        assert exc.value.status_code == 400
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_claims_is_rejected(self):
        db = make_db()
        with pytest.raises(HTTPException) as exc:
            await service.request_to_join_handler(PROPERTY_ID, "ABC123", db, None)
        assert exc.value.status_code == 401
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_invalid_code_rolls_back(self):
        db = make_db([result(scalar=None)])
        with pytest.raises(HTTPException) as exc:
            await service.request_to_join_handler(PROPERTY_ID, "BADCODE", db, claims())
        assert exc.value.status_code == 404
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_property_admin_can_create_pending_request(self):
        neighbourhood = SimpleNamespace(id=NEIGHBOURHOOD_ID)
        user = SimpleNamespace(id=USER_ID)
        property_obj = SimpleNamespace(neighbourhood_id=None)
        property_user = SimpleNamespace(is_admin=True)
        db = make_db([
            result(scalar=neighbourhood),
            result(scalar=user),
            result(first=(property_obj, property_user)),
            result(scalar=None),
        ])

        def add(obj):
            if hasattr(obj, "status"):
                obj.id = REQUEST_ID
                obj.created_at = datetime.now(timezone.utc)

        db.add.side_effect = add
        with patch.object(service, "create_audit_log_item", new=AsyncMock()):
            response = await service.request_to_join_handler(
                PROPERTY_ID, " ABC123 ", db, claims()
            )

        assert response.id == REQUEST_ID
        assert response.property_id == PROPERTY_ID
        assert response.neighbourhood_id == NEIGHBOURHOOD_ID
        assert response.user_id == USER_ID
        assert response.status == "PENDING"
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_non_admin_property_user_is_rejected(self):
        db = make_db([
            result(scalar=SimpleNamespace(id=NEIGHBOURHOOD_ID)),
            result(scalar=SimpleNamespace(id=USER_ID)),
            result(first=None),
        ])
        with pytest.raises(HTTPException) as exc:
            await service.request_to_join_handler(PROPERTY_ID, "ABC123", db, claims())
        assert exc.value.status_code == 403
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_property_already_in_neighbourhood_is_rejected(self):
        db = make_db([
            result(scalar=SimpleNamespace(id=NEIGHBOURHOOD_ID)),
            result(scalar=SimpleNamespace(id=USER_ID)),
            result(first=(SimpleNamespace(neighbourhood_id=NEIGHBOURHOOD_ID), SimpleNamespace())),
        ])
        with pytest.raises(HTTPException) as exc:
            await service.request_to_join_handler(PROPERTY_ID, "ABC123", db, claims())
        assert exc.value.status_code == 409
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_existing_pending_request_is_rejected(self):
        db = make_db([
            result(scalar=SimpleNamespace(id=NEIGHBOURHOOD_ID)),
            result(scalar=SimpleNamespace(id=USER_ID)),
            result(first=(SimpleNamespace(neighbourhood_id=None), SimpleNamespace())),
            result(scalar=SimpleNamespace(status=JoinRequestStatus.PENDING)),
        ])
        with pytest.raises(HTTPException) as exc:
            await service.request_to_join_handler(PROPERTY_ID, "ABC123", db, claims())
        assert exc.value.status_code == 409
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_integrity_error_is_converted_to_conflict(self):
        db = make_db([
            result(scalar=SimpleNamespace(id=NEIGHBOURHOOD_ID)),
            result(scalar=SimpleNamespace(id=USER_ID)),
            result(first=(SimpleNamespace(neighbourhood_id=None), SimpleNamespace())),
            result(scalar=None),
        ])
        db.flush.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
        with pytest.raises(HTTPException) as exc:
            await service.request_to_join_handler(PROPERTY_ID, "ABC123", db, claims())
        assert exc.value.status_code == 409
        db.rollback.assert_awaited_once()


class TestResolveJoinRequestAdditional:
    ADMIN_CLAIMS = {
        "id": str(USER_ID),
        "sub": "admin-sub",
        "custom:role": "NEIGHBOURHOOD_ADMIN",
    }

    @pytest.mark.asyncio
    async def test_missing_request_id_and_invalid_action_are_rejected(self):
        db = make_db()
        with pytest.raises(HTTPException) as missing_id:
            await service.resolve_join_request_handler(None, "APPROVE", db, self.ADMIN_CLAIMS)
        assert missing_id.value.status_code == 400

        with pytest.raises(HTTPException) as invalid_action:
            await service.resolve_join_request_handler(REQUEST_ID, "MAYBE", db, self.ADMIN_CLAIMS)
        assert invalid_action.value.status_code == 400

    @pytest.mark.asyncio
    async def test_request_not_found_is_rejected(self):
        db = make_db([result(scalar=None)])
        with pytest.raises(HTTPException) as exc:
            await service.resolve_join_request_handler(REQUEST_ID, "APPROVE", db, self.ADMIN_CLAIMS)
        assert exc.value.status_code == 404
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_already_resolved_request_is_rejected(self):
        db = make_db([result(scalar=make_request(JoinRequestStatus.APPROVED))])
        with pytest.raises(HTTPException) as exc:
            await service.resolve_join_request_handler(REQUEST_ID, "DENY", db, self.ADMIN_CLAIMS)
        assert exc.value.status_code == 409
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_non_admin_cannot_resolve_request(self):
        db = make_db([
            result(scalar=make_request()),
            result(scalar=None),
        ])
        with pytest.raises(HTTPException) as exc:
            await service.resolve_join_request_handler(REQUEST_ID, "DENY", db, self.ADMIN_CLAIMS)
        assert exc.value.status_code == 403
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approve_updates_property_and_adds_resident_membership(self):
        join_request = make_request()
        property_obj = SimpleNamespace(id=PROPERTY_ID, neighbourhood_id=None)
        db = make_db([
            result(scalar=join_request),
            result(scalar=SimpleNamespace(role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN)),
            result(scalar=property_obj),
            result(scalar=None),
        ])

        with patch.object(service, "create_audit_log_item", new=AsyncMock()):
            response = await service.resolve_join_request_handler(
                REQUEST_ID, "APPROVE", db, self.ADMIN_CLAIMS
            )

        assert response.status == "APPROVED"
        assert property_obj.neighbourhood_id == NEIGHBOURHOOD_ID
        assert join_request.resolved_at is not None
        assert any(
            getattr(call.args[0], "role", None) == NeighbourhoodRole.RESIDENT
            for call in db.add.call_args_list
        )
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approve_rejects_missing_property(self):
        db = make_db([
            result(scalar=make_request()),
            result(scalar=SimpleNamespace()),
            result(scalar=None),
        ])
        with pytest.raises(HTTPException) as exc:
            await service.resolve_join_request_handler(
                REQUEST_ID, "APPROVE", db, self.ADMIN_CLAIMS
            )
        assert exc.value.status_code == 404
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approve_rejects_property_already_assigned(self):
        db = make_db([
            result(scalar=make_request()),
            result(scalar=SimpleNamespace()),
            result(scalar=SimpleNamespace(neighbourhood_id=uuid.uuid4())),
        ])
        with pytest.raises(HTTPException) as exc:
            await service.resolve_join_request_handler(
                REQUEST_ID, "APPROVE", db, self.ADMIN_CLAIMS
            )
        assert exc.value.status_code == 409
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deny_marks_request_rejected(self):
        join_request = make_request()
        db = make_db([
            result(scalar=join_request),
            result(scalar=SimpleNamespace(role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN)),
        ])

        with patch.object(service, "create_audit_log_item", new=AsyncMock()):
            response = await service.resolve_join_request_handler(
                REQUEST_ID, "DENY", db, self.ADMIN_CLAIMS
            )

        assert response.status == "REJECTED"
        assert join_request.resolved_at is not None
        db.commit.assert_awaited_once()


class TestJoinCodeHandlersAdditional:
    ADMIN_CLAIMS = {"id": str(USER_ID)}

    @pytest.mark.asyncio
    async def test_get_join_code_requires_claims(self):
        with pytest.raises(HTTPException) as exc:
            await service.get_join_code_handler(NEIGHBOURHOOD_ID, make_db(), None)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_join_code_requires_local_user(self):
        db = make_db([result(scalar=None)])
        with pytest.raises(HTTPException) as exc:
            await service.get_join_code_handler(NEIGHBOURHOOD_ID, db, self.ADMIN_CLAIMS)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_join_code_requires_admin_membership(self):
        db = make_db([
            result(scalar=SimpleNamespace(id=USER_ID)),
            result(scalar=None),
        ])
        with pytest.raises(HTTPException) as exc:
            await service.get_join_code_handler(NEIGHBOURHOOD_ID, db, self.ADMIN_CLAIMS)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_join_code_returns_code_for_admin(self):
        db = make_db([
            result(scalar=SimpleNamespace(id=USER_ID)),
            result(scalar=SimpleNamespace(join_code="ABC12345")),
        ])
        response = await service.get_join_code_handler(NEIGHBOURHOOD_ID, db, self.ADMIN_CLAIMS)
        assert response.join_code == "ABC12345"

    @pytest.mark.asyncio
    async def test_get_join_code_converts_unexpected_error_to_500(self):
        db = make_db()
        db.execute.side_effect = RuntimeError("database unavailable")
        with pytest.raises(HTTPException) as exc:
            await service.get_join_code_handler(NEIGHBOURHOOD_ID, db, self.ADMIN_CLAIMS)
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_regenerate_join_code_retries_collision(self):
        neighbourhood = SimpleNamespace(join_code="OLD_CODE")
        db = make_db([
            result(scalar=SimpleNamespace(id=USER_ID)),
            result(scalar=neighbourhood),
            result(scalar=SimpleNamespace(id=uuid.uuid4())),
            result(scalar=None),
        ])

        with patch.object(service.secrets, "choice", return_value="A"):
            response = await service.regenerate_join_code_handler(
                NEIGHBOURHOOD_ID, db, self.ADMIN_CLAIMS
            )

        assert response.join_code == "AAAAAAAA"
        assert neighbourhood.join_code == "AAAAAAAA"
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(neighbourhood)

    @pytest.mark.asyncio
    async def test_regenerate_join_code_converts_integrity_error(self):
        db = make_db()
        db.execute.side_effect = IntegrityError("select", {}, Exception("db"))
        with pytest.raises(HTTPException) as exc:
            await service.regenerate_join_code_handler(
                NEIGHBOURHOOD_ID, db, self.ADMIN_CLAIMS
            )
        assert exc.value.status_code == 500
        db.rollback.assert_awaited_once()