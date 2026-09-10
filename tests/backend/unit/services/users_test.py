import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch, AsyncMock
from app.models.user import UserRole
from app.schemas.user import UpdateUserSettingsReq
from app.services.user_service import create_user, get_current_user_settings_handler, update_current_user_settings_handler

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from app.models.neighbourhood_user import NeighbourhoodRole

from app.services.user_service import (
    get_user_by_id_handler,
    get_current_user_context_handler,
)

class TestCreateUser:
    def setup_method(self):
        """Runs before each test method - same as allt he other tests"""

        self.mock_db = Mock()

        self.mock_db.add = Mock()
        self.mock_db.execute = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        result = Mock()
        result.scalar_one_or_none.return_value = None
        self.mock_db.execute.return_value = result

        self.mock_user = Mock()
        self.mock_user.email = "test@email.com"
        self.mock_user.first_name = "John"
        self.mock_user.last_name = "Doe"
        self.mock_user.cognito_sub = "test-sub-123"


    @pytest.mark.asyncio
    async def test_happy_path(self):
        user = await create_user(
            email = "test@email.com",
            first_name = "John",
            last_name = "Doe",
            cognito_sub = "test-sub-123",
            db = self.mock_db
        )

        assert user is not None
        assert user.email == "test@email.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"

        assert self.mock_db.add.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_email(self):
        with patch('app.services.user_service') as _MockUser:

            with pytest.raises(HTTPException) as exception:
                _ = await create_user(
                    email = "",
                    first_name = "John",
                    last_name = "Doe",
                    cognito_sub = "test-sub-123",
                    db = self.mock_db
                )

            assert exception.value.status_code == 400

            assert self.mock_db.add.call_count == 0
            assert self.mock_db.refresh.call_count == 0
            assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_first_name(self):
        with patch('app.services.user_service') as _MockUser:

            with pytest.raises(HTTPException) as exception:
                _ = await create_user(
                    email = "test@gmail.com",
                    first_name = "",
                    last_name = "Doe",
                    cognito_sub = "test-sub-123",
                    db = self.mock_db
                )

            assert exception.value.status_code == 400

            assert self.mock_db.add.call_count == 0
            assert self.mock_db.refresh.call_count == 0
            assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_last_name(self):
        with patch('app.services.user_service') as _MockUser:

            with pytest.raises(HTTPException) as exception:
                _ = await create_user(
                    email = "test@gmail.com",
                    first_name = "John",
                    last_name = "",
                    cognito_sub = "test-sub-123",
                    db = self.mock_db
                )

            assert exception.value.status_code == 400

            assert self.mock_db.add.call_count == 0
            assert self.mock_db.refresh.call_count == 0
            assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_cognito_sub(self):

        with pytest.raises(HTTPException) as exception:
            await create_user(
                email = "test@gmail.com",
                first_name = "John",
                last_name = "Doe",
                cognito_sub = "",
                db = self.mock_db
            )

        assert exception.value.status_code == 400

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_no_db(self):
        with pytest.raises(HTTPException) as exception:
            await create_user(
                email = "test@gmail.com",
                first_name = "John",
                last_name = "Doe",
                cognito_sub = "test-sub-123",
                db = None
            )

        assert exception.value.status_code == 500

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0


class TestUserSettings:
    def setup_method(self):
        """Runs before each test method"""

        self.mock_db = Mock()

        self.mock_db.execute = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.refresh = AsyncMock()

        self.mock_user = Mock()
        self.mock_user.first_name = "John"
        self.mock_user.last_name = "Doe"
        self.mock_user.email = "test@email.com"
        self.mock_user.phone_number = None
        self.mock_user.system_role = UserRole.RESIDENT

        result = Mock()
        result.scalar_one_or_none.return_value = self.mock_user
        self.mock_db.execute.return_value = result

        self.claims = {
            "id": "550e8400-e29b-41d4-a716-446655440000"
        }

    @pytest.mark.asyncio
    async def test_get_user_settings(self):
        settings = await get_current_user_settings_handler(
            claims=self.claims,
            db=self.mock_db,
        )

        assert settings.first_name == "John"
        assert settings.last_name == "Doe"
        assert settings.email == "test@email.com"
        assert settings.phone_number is None
        assert settings.system_role == UserRole.RESIDENT

        assert self.mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_get_user_settings_user_not_found(self):
        result = Mock()
        result.scalar_one_or_none.return_value = None
        self.mock_db.execute.return_value = result

        with pytest.raises(HTTPException) as exception:
            await get_current_user_settings_handler(
                claims=self.claims,
                db=self.mock_db,
            )

        assert exception.value.status_code == 401


    @pytest.mark.asyncio
    async def test_update_user_settings(self):
        data = UpdateUserSettingsReq(
            first_name="Jane",
            last_name="Smith",
            phone_number="+27820000000",
        )

        settings = await update_current_user_settings_handler(
            data=data,
            claims=self.claims,
            db=self.mock_db,
        )

        assert self.mock_user.first_name == "Jane"
        assert self.mock_user.last_name == "Smith"
        assert self.mock_user.phone_number == "+27820000000"

        assert settings.first_name == "Jane"
        assert settings.last_name == "Smith"
        assert settings.phone_number == "+27820000000"

        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1

    @pytest.mark.asyncio
    async def test_update_user_settings_with_empty_phone_number(self):
        data = UpdateUserSettingsReq(
            first_name="John",
            last_name="Doe",
            phone_number=" ",
        )

        await update_current_user_settings_handler(
            data=data,
            claims=self.claims,
            db=self.mock_db,
        )

        assert self.mock_user.phone_number is None

    @pytest.mark.asyncio
    async def test_update_user_settings_with_empty_first_name(self):
        data = UpdateUserSettingsReq(
            first_name=" ",
            last_name="Doe",
            phone_number=None,
        )

        with pytest.raises(HTTPException) as exception:
            await update_current_user_settings_handler(
                data=data,
                claims=self.claims,
                db=self.mock_db,
            )

        assert exception.value.status_code == 400
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_update_user_settings_with_empty_last_name(self):
        data = UpdateUserSettingsReq(
            first_name="John",
            last_name=" ",
            phone_number=None,
        )

        with pytest.raises(HTTPException) as exception:
            await update_current_user_settings_handler(
                data=data,
                claims=self.claims,
                db=self.mock_db,
            )

        assert exception.value.status_code == 400
        assert self.mock_db.commit.call_count == 0

@pytest.mark.asyncio
async def test_create_user_returns_existing_user_without_creating_duplicate():
    existing_user = SimpleNamespace(
        id=uuid4(),
        email="existing@example.com",
        first_name="Existing",
        last_name="User",
        cognito_sub="existing-sub",
        system_role=UserRole.RESIDENT,
    )

    result = Mock()
    result.scalar_one_or_none.return_value = existing_user

    db = Mock()
    db.execute = AsyncMock(return_value=result)
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    response = await create_user(
        email="existing@example.com",
        first_name="New",
        last_name="User",
        cognito_sub="new-sub",
        db=db,
    )

    assert response is existing_user
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_user_rolls_back_on_integrity_error():
    db = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = None

    db.execute = AsyncMock(return_value=result)
    db.add = Mock()
    db.commit = AsyncMock(
        side_effect=IntegrityError(
            "insert user",
            {},
            RuntimeError("duplicate user"),
        )
    )
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await create_user(
            email="new@example.com",
            first_name="New",
            last_name="User",
            cognito_sub="new-sub",
            db=db,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to create user"
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_id_rejects_missing_database():
    with pytest.raises(HTTPException) as exc_info:
        await get_user_by_id_handler(
            user_id=uuid4(),
            db=None,
            claims={},
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "No database session"


@pytest.mark.asyncio
async def test_get_user_by_id_returns_404_when_user_missing():
    db = Mock()
    db.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_user_by_id_handler(
            user_id=uuid4(),
            db=db,
            claims={},
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_get_user_by_id_returns_user_details():
    user_id = uuid4()
    created_at = datetime(2026, 1, 1)

    user = SimpleNamespace(
        id=user_id,
        email="user@example.com",
        cognito_sub="cognito-sub",
        system_role=UserRole.RESIDENT,
        created_at=created_at,
    )

    db = Mock()
    db.get = AsyncMock(return_value=user)

    response = await get_user_by_id_handler(
        user_id=user_id,
        db=db,
        claims={"sub": "cognito-sub"},
    )

    assert response.id == user_id
    assert response.email == "user@example.com"
    assert response.cognito_sub == "cognito-sub"
    assert response.role == UserRole.RESIDENT
    assert response.created_at == created_at


@pytest.mark.asyncio
async def test_get_current_user_context_returns_neighbourhoods_and_properties():
    user_id = uuid4()
    property_id = uuid4()
    neighbourhood_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        first_name="John",
        last_name="Doe",
        system_role=UserRole.RESIDENT,
    )

    membership = SimpleNamespace(
        user_id=user_id,
        neighbourhood_id=neighbourhood_id,
        role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
    )

    property_membership = SimpleNamespace(
        user_id=user_id,
        property_id=property_id,
        is_admin=True,
    )

    property_obj = SimpleNamespace(
        id=property_id,
        address="123 Test Street",
        neighbourhood_id=neighbourhood_id,
    )

    user_result = Mock()
    user_result.scalar_one_or_none.return_value = user

    neighbourhood_result = Mock()
    neighbourhood_result.all.return_value = [
        (membership, "Test Neighbourhood"),
    ]

    property_result = Mock()
    property_result.all.return_value = [
        (property_membership, property_obj),
    ]

    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            user_result,
            neighbourhood_result,
            property_result,
        ]
    )

    response = await get_current_user_context_handler(
        claims={"id": str(user_id)},
        db=db,
    )

    assert response.user.id == user_id
    assert response.user.name == "John Doe"
    assert response.user.system_role == UserRole.RESIDENT

    assert len(response.properties) == 1
    assert response.properties[0].id == property_id
    assert response.properties[0].address == "123 Test Street"
    assert response.properties[0].is_admin is True

    assert response.properties[0].neighbourhood is not None
    assert response.properties[0].neighbourhood.id == neighbourhood_id
    assert response.properties[0].neighbourhood.name == "Test Neighbourhood"
    assert (
        response.properties[0].neighbourhood.role
        == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
    )


@pytest.mark.asyncio
async def test_get_current_user_context_returns_401_when_user_missing():
    user_result = Mock()
    user_result.scalar_one_or_none.return_value = None

    db = Mock()
    db.execute = AsyncMock(return_value=user_result)

    user_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_context_handler(
            claims={"id": str(user_id)},
            db=db,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Authenticated user not found in databse"
    )


@pytest.mark.asyncio
async def test_update_user_settings_rejects_missing_user():
    db = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    data = UpdateUserSettingsReq(
        first_name="John",
        last_name="Doe",
        phone_number=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        await update_current_user_settings_handler(
            data=data,
            claims={"id": str(uuid4())},
            db=db,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Authenticated user not found in database"
    )
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()