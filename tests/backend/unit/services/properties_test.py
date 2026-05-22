from fastapi import HTTPException
import pytest
from unittest.mock import Mock, patch
from app.services.property_service import create_property_handler, get_user_properties_handler
from app.models.property import PropertyTypeEnum
from uuid import uuid4

# create_property_handler tests
class TestCreateProperty:
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
    async def test_happy_path(self): 
        with patch('app.services.property_service.Property') as MockProperty:
            # patch('app.services.property_service.PropertyUser') as _MockPropertyUser:
            #create the vars and whatnot
            mock_prop = Mock()
            mock_prop.id = uuid4()
            MockProperty.return_value = mock_prop

            await create_property_handler(
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
            patch('app.services.property_service.PropertyUser') as _MockPropertyUser:

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
            patch('app.services.property_service.PropertyUser') as _MockPropertyUser:

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
            patch('app.services.property_service.PropertyUser') as _MockPropertyUser:

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


# get_user_properties_handler tests
class TestGetUserProperties:
    def setup_method(self):
        """Runs before each test method"""
        self.mock_db = Mock()
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.claims = {"sub": "cognito-sub-123"}

    @pytest.mark.asyncio
    async def test_happy_path_with_properties(self):
        """Test fetching properties when user has multiple properties"""

        self.mock_db.execute.return_value.scalar_one_or_none.return_value = self.mock_user

        mock_prop1 = Mock()
        mock_prop1.id = uuid4()
        mock_prop1.address = "123 Main St"
        mock_prop1.neighbourhood_id = uuid4()
        mock_prop1.property_type = PropertyTypeEnum.PRIVATE
        mock_prop1.created_at = Mock()

        mock_prop2 = Mock()
        mock_prop2.id = uuid4()
        mock_prop2.address = "456 Oak Ave"
        mock_prop2.neighbourhood_id = None
        mock_prop2.property_type = PropertyTypeEnum.PUBLIC
        mock_prop2.created_at = Mock()

        self.mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_prop1, mock_prop2]

        properties = await get_user_properties_handler(self.claims, self.mock_db)

        assert len(properties) == 2
        assert properties[0].address == "123 Main St"
        assert properties[1].address == "456 Oak Ave"

    @pytest.mark.asyncio
    async def test_happy_path_empty_properties(self):
        """Test when user has no properties"""
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = self.mock_user
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = []

        properties = await get_user_properties_handler(self.claims, self.mock_db)

        assert len(properties) == 0

    @pytest.mark.asyncio
    async def test_no_claims(self):
        """Test when claims are not provided"""
        with pytest.raises(HTTPException) as exc_info:
            await get_user_properties_handler(None, self.mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        """Test when user does not exist"""
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_user_properties_handler(self.claims, self.mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_single_property(self):
        """Test fetching when user has a single property"""
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = self.mock_user

        mock_prop = Mock()
        mock_prop.id = uuid4()
        mock_prop.address = "789 Pine St"
        mock_prop.neighbourhood_id = uuid4()
        mock_prop.property_type = PropertyTypeEnum.PRIVATE
        mock_prop.created_at = Mock()

        self.mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_prop]

        properties = await get_user_properties_handler(self.claims, self.mock_db)

        assert len(properties) == 1
        assert properties[0].address == "789 Pine St"