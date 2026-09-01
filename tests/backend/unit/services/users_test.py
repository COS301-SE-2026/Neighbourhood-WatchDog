import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch, AsyncMock
from app.models.user import UserRole
from app.schemas.user import UpdateUserSettingsReq
from app.services.user_service import create_user, get_current_user_settings_handler, update_current_user_settings_handler

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