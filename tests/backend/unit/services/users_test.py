import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from app.services.user_service import create_user

class TestCreateUser:
    def setup_method(self):
        """Runs before each test method - same as allt he other tests"""

        self.mock_db = Mock()
        
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()

        self.mock_user = Mock()
        self.mock_user.email = "test@email.com"
        self.mock_user.first_name = "John"
        self.mock_user.last_name = "Doe"
        self.mock_user.cognito_sub = "test-sub-123"

        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None

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

            self.mock_db.execute.return_value.scalar_one_or_none.return_value = None
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
    async def test_empty_first_namel(self):
        with patch('app.services.user_service') as _MockUser:

            self.mock_db.execute.return_value.scalar_one_or_none.return_value = None
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

            self.mock_db.execute.return_value.scalar_one_or_none.return_value = None
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

        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None
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
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None
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