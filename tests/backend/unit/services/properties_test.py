from fastapi import HTTPException
import pytest, pytest_asyncio
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError
from app.services.property_service import create_property_handler
from app.models.property import PropertyTypeEnum
from uuid import uuid4

# create_property_handler tests
class TestCreateProper:
    def setup_method(self):
        """Runs before each test method"""
        self.mock_db = Mock()

        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = self.mock_user

        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.rollback = Mock()

        self.claims = {"sub": "cognito-sub-123"}

    @pytest.mark.asyncio
    async def test_happy_case(self): 
        with patch('app.services.property_service.Property') as MockProperty, \
            patch('app.services.property_service.PropertyUser') as MockPropertyUser:
            #create the vars and whatnot
            mock_prop = Mock()
            mock_prop.id = uuid4()
            MockProperty.return_value = mock_prop

            property = await create_property_handler(
                "100 Test Street",
                PropertyTypeEnum.PRIVATE,
                self.claims,
                self.mock_db
            )

            assert self.mock_db.add.call_count == 2
            assert self.mock_db.flush.call_count == 2
            assert self.mock_db.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_empty_address(self):
        with patch('app.services.property_service.Property') as MockProperty, \
            patch('app.services.property_service.PropertyUser') as MockPropertyUser:

            mock_prop = Mock()
            MockProperty.return_value = mock_prop

            # expecting an exception bad req
            with pytest.raises(HTTPException) as exc_info:
                await create_property_handler(
                    "",
                    PropertyTypeEnum.PRIVATE,
                    self.claims,
                    self.mock_db
                )
            assert exc_info.value.status_code == 400
            assert self.mock_db.add.call_count == 0
            assert self.mock_db.flush.call_count == 0
            assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_no_claims(self):
        with patch('app.services.property_service.Property') as MockProperty, \
            patch('app.services.property_service.PropertyUser') as MockPropertyUser:

            mock_prop = Mock()
            MockProperty.return_value = mock_prop

            # expecting an exception bad req
            with pytest.raises(HTTPException) as exc_info:
                await create_property_handler(
                    "test 123",
                    None,
                    self.claims,
                    self.mock_db
                )
            assert exc_info.value.status_code == 400
            assert self.mock_db.add.call_count == 0
            assert self.mock_db.flush.call_count == 0
            assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_no_claim(self):
        with patch('app.services.property_service.Property') as MockProperty, \
            patch('app.services.property_service.PropertyUser') as MockPropertyUser:

            mock_prop = Mock()
            MockProperty.return_value = mock_prop

            # expecting an exception bad req
            with pytest.raises(HTTPException) as exc_info:
                await create_property_handler(
                    "100 Test Street",
                    PropertyTypeEnum.PRIVATE,
                    None,
                    self.mock_db
                )
            assert exc_info.value.status_code == 401
            assert self.mock_db.add.call_count == 0
            assert self.mock_db.flush.call_count == 0
            assert self.mock_db.commit.call_count == 0