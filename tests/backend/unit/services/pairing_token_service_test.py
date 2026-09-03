import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.camera import CameraVisibilityEnum
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.models.pairing_token import PairingToken
from app.services import pairing_token as service


PROPERTY_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
CAMERA_ID = uuid.uuid4()


def db_result(*, scalar=None, rows=()):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar
    result.scalars.return_value.all.return_value = list(rows)
    return result


def make_db(results=()):
    db = MagicMock()
    db.execute = AsyncMock(side_effect=list(results))
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    return db


def integrity_error():
    return IntegrityError("duplicate key", {}, Exception("duplicate"))


def make_property():
    return SimpleNamespace(
        id=PROPERTY_ID,
        address="123 Test Street",
        neighbourhood_id=uuid.uuid4(),
    )


def make_camera():
    return SimpleNamespace(
        id=CAMERA_ID,
        name="Front Gate",
        property_id=PROPERTY_ID,
        visibility=CameraVisibilityEnum.PRIVATE,
        location="Driveway",
        enabled=True,
        rtsp_url="encrypted-url",
        created_at=datetime.now(timezone.utc),
    )


class TestPairingTokenHelpers:
    def test_generate_pairing_token_has_expected_format(self):
        choices = iter("ABCDEFGHI")
        with patch.object(service.secrets, "choice", side_effect=lambda _: next(choices)) as choose:
            token = service.generate_pairing_token()

        assert token == "ABC-DEF-GHI"
        assert choose.call_count == 9
        alphabet = choose.call_args.args[0]
        assert all(character not in alphabet for character in "01ILil")

    def test_gen_api_key_adds_watchdog_prefix(self):
        with patch.object(service.secrets, "token_urlsafe", return_value="known-secret"):
            assert service.gen_api_key() == "wd_known-secret"

    def test_hash_api_key_returns_sha256(self):
        expected = hashlib.sha256(b"known-secret").hexdigest()
        assert service.hash_api_key("known-secret") == expected


class TestGetPairingTokenHandler:
    CLAIMS = {"sub": "cognito-sub"}

    @pytest.mark.asyncio
    async def test_missing_property_id_is_rejected_without_db_access(self):
        db = make_db()
        with pytest.raises(HTTPException) as exc:
            await service.get_pairing_token_handler(None, db, self.CLAIMS)
        assert exc.value.status_code == 400
        db.execute.assert_not_awaited()
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_db_is_rejected(self):
        with pytest.raises(HTTPException) as exc:
            await service.get_pairing_token_handler(PROPERTY_ID, None, self.CLAIMS)
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_unknown_property_is_rejected(self):
        db = make_db([db_result(scalar=None)])
        with pytest.raises(HTTPException) as exc:
            await service.get_pairing_token_handler(PROPERTY_ID, db, self.CLAIMS)
        assert exc.value.status_code == 404
        db.add.assert_not_called()
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_creates_token_audits_and_commits(self):
        property_obj = make_property()
        user = SimpleNamespace(id=USER_ID)
        db = make_db([
            db_result(scalar=property_obj),
            db_result(scalar=user),
        ])
        token_id = uuid.uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        def add(obj):
            if isinstance(obj, PairingToken):
                obj.id = token_id
                obj.expires_at = expires_at

        db.add.side_effect = add
        audit = AsyncMock()

        with (
            patch.object(service, "generate_pairing_token", return_value="ABC-DEF-GHI"),
            patch.object(service, "create_audit_log_item", new=audit),
        ):
            response = await service.get_pairing_token_handler(
                PROPERTY_ID, db, self.CLAIMS
            )

        assert response.status == 200
        assert response.data.token == "ABC-DEF-GHI"
        assert response.data.expires_at == expires_at
        token_record = db.add.call_args.args[0]
        assert isinstance(token_record, PairingToken)
        assert token_record.property_id == PROPERTY_ID
        audit.assert_awaited_once()
        assert audit.call_args.kwargs["user_id"] == USER_ID
        assert audit.call_args.kwargs["target_entity_id"] == token_id
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_collision_retries_then_succeeds(self):
        property_obj = make_property()
        user = SimpleNamespace(id=USER_ID)
        db = make_db([
            db_result(scalar=property_obj),
            db_result(scalar=user),
        ])
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        token_ids = iter([uuid.uuid4(), uuid.uuid4()])
        flush_results = [integrity_error(), None]
        db.flush.side_effect = flush_results

        def add(obj):
            if isinstance(obj, PairingToken):
                obj.id = next(token_ids)
                obj.expires_at = expires_at

        db.add.side_effect = add
        with (
            patch.object(
                service,
                "generate_pairing_token",
                side_effect=["AAA-BBB-CCC", "DDD-EEE-FFF"],
            ),
            patch.object(service, "create_audit_log_item", new=AsyncMock()),
        ):
            response = await service.get_pairing_token_handler(
                PROPERTY_ID, db, self.CLAIMS
            )

        assert response.data.token == "DDD-EEE-FFF"
        assert db.flush.await_count == 2
        db.rollback.assert_awaited_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ten_collisions_raise_runtime_error(self):
        property_obj = make_property()
        db = make_db([db_result(scalar=property_obj)])
        db.flush.side_effect = [integrity_error() for _ in range(10)]

        with patch.object(service, "generate_pairing_token", return_value="AAA-BBB-CCC"):
            with pytest.raises(RuntimeError, match="Failed to generate unique"):
                await service.get_pairing_token_handler(
                    PROPERTY_ID, db, self.CLAIMS
                )

        assert db.flush.await_count == 10
        assert db.rollback.await_count == 10
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_user_raises_404(self):
        property_obj = make_property()
        db = make_db([
            db_result(scalar=property_obj),
            db_result(scalar=None),
        ])
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.add.side_effect = lambda obj: setattr(obj, "expires_at", expires_at)

        with (
            patch.object(service, "generate_pairing_token", return_value="AAA-BBB-CCC"),
            patch.object(service, "create_audit_log_item", new=AsyncMock()),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.get_pairing_token_handler(
                    PROPERTY_ID, db, self.CLAIMS
                )

        assert exc.value.status_code == 404
        db.commit.assert_not_awaited()


class TestPairAgentHandler:
    @pytest.mark.asyncio
    async def test_missing_db_is_rejected(self):
        with pytest.raises(HTTPException) as exc:
            await service.pair_agent_handler("ABC-DEF-GHI", None)
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_unknown_token_rolls_back(self):
        db = make_db([db_result(scalar=None)])
        with pytest.raises(HTTPException) as exc:
            await service.pair_agent_handler("BAD-TOK-EN", db)
        assert exc.value.status_code == 400
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_expired_token_rolls_back(self):
        token = SimpleNamespace(
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            used_at=None,
        )
        db = make_db([db_result(scalar=token)])
        with pytest.raises(HTTPException) as exc:
            await service.pair_agent_handler("OLD-TOK-EN", db)
        assert exc.value.status_code == 400
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_used_token_rolls_back(self):
        token = SimpleNamespace(
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            used_at=datetime.now(timezone.utc),
        )
        db = make_db([db_result(scalar=token)])
        with pytest.raises(HTTPException) as exc:
            await service.pair_agent_handler("USED-TOKEN", db)
        assert exc.value.status_code == 400
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_missing_property_rolls_back(self):
        token = SimpleNamespace(
            property_id=PROPERTY_ID,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            used_at=None,
        )
        db = make_db([
            db_result(scalar=token),
            db_result(scalar=None),
        ])
        with pytest.raises(HTTPException) as exc:
            await service.pair_agent_handler("ABC-DEF-GHI", db)
        assert exc.value.status_code == 404
        db.rollback.assert_awaited_once()
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_success_returns_hashed_credentials_and_cameras(self):
        token = SimpleNamespace(
            property_id=PROPERTY_ID,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            used_at=None,
        )
        property_obj = make_property()
        camera = make_camera()
        db = make_db([
            db_result(scalar=token),
            db_result(scalar=property_obj),
            db_result(rows=[camera]),
        ])
        created_at = datetime.now(timezone.utc)

        def add(obj):
            if isinstance(obj, EdgeAgentCredential):
                obj.id = uuid.uuid4()
                obj.created_at = created_at

        db.add.side_effect = add

        with patch.object(service, "gen_api_key", return_value="wd_test-key"):
            response = await service.pair_agent_handler("ABC-DEF-GHI", db)

        assert response.status == 201
        assert response.data.property_id == PROPERTY_ID
        assert response.data.address == property_obj.address
        assert response.data.api_key == "wd_test-key"
        assert response.data.cameras[0].id == CAMERA_ID
        assert response.data.cameras[0].neighbourhood_id == property_obj.neighbourhood_id
        assert token.used_at is not None
        credential = next(
            call.args[0]
            for call in db.add.call_args_list
            if isinstance(call.args[0], EdgeAgentCredential)
        )
        assert credential.property_id == PROPERTY_ID
        assert credential.key_hash == service.hash_api_key("wd_test-key")
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_success_supports_property_without_cameras(self):
        token = SimpleNamespace(
            property_id=PROPERTY_ID,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            used_at=None,
        )
        db = make_db([
            db_result(scalar=token),
            db_result(scalar=make_property()),
            db_result(rows=[]),
        ])
        created_at = datetime.now(timezone.utc)
        db.add.side_effect = lambda obj: setattr(obj, "created_at", created_at)

        with patch.object(service, "gen_api_key", return_value="wd_test-key"):
            response = await service.pair_agent_handler("ABC-DEF-GHI", db)

        assert response.status == 201
        assert response.data.cameras == []

    @pytest.mark.asyncio
    async def test_credential_integrity_error_becomes_500(self):
        token = SimpleNamespace(
            property_id=PROPERTY_ID,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            used_at=None,
        )
        property_obj = make_property()
        db = make_db([
            db_result(scalar=token),
            db_result(scalar=property_obj),
        ])
        db.flush.side_effect = [None, integrity_error()]

        with patch.object(service, "gen_api_key", return_value="wd_test-key"):
            with pytest.raises(HTTPException) as exc:
                await service.pair_agent_handler("ABC-DEF-GHI", db)

        assert exc.value.status_code == 500
        db.rollback.assert_awaited_once()