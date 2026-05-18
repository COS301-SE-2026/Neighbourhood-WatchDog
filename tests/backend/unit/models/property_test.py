from pydantic import ValidationError
import pytest
from uuid import uuid4
from app.schemas.property import CreatePropertyReq, PropertyRes, CreatePropertyRes
from app.models.property import PropertyTypeEnum
from datetime import datetime

class TestCreatePropertyReq:
    def test_valid_model_private(self):
        """Happy path with PRIVATE property"""
        address = "123 Main Street"
        property_type = PropertyTypeEnum.PRIVATE

        req = CreatePropertyReq(
            address=address,
            property_type=property_type
        )

        assert req.address == address
        assert req.property_type == property_type

    def test_valid_model_public(self):
        """Happy path with PUBLIC property"""
        address = "456 Oak Avenue"
        property_type = PropertyTypeEnum.PUBLIC

        req = CreatePropertyReq(
            address=address,
            property_type=property_type
        )

        assert req.address == address
        assert req.property_type == property_type

    def test_missing_address(self):
        """Test that missing address raises an error"""
        with pytest.raises(ValidationError):
            CreatePropertyReq(
                address=None,
                property_type=PropertyTypeEnum.PRIVATE
            )

    def test_missing_property_type(self):
        """Test that missing property_type raises ValidationError"""
        with pytest.raises(ValidationError):
            CreatePropertyReq(
                address="123 Main Street"
                # Missing property_type
            )

    def test_invalid_property_type(self):
        """Test that invalid property_type raises ValidationError"""
        with pytest.raises(ValidationError):
            CreatePropertyReq(
                address="123 Main Street",
                property_type="invalid_type"
            )

    def test_empty_string_address(self):
        """Test that empty address raises ValidationError"""
        with pytest.raises(ValidationError):
            CreatePropertyReq(
                address="",
                property_type=PropertyTypeEnum.PRIVATE
            )

    def test_whitespace_only_address(self):
        """Test that whitespace-only address is stripped and rejected"""
        with pytest.raises(ValidationError):
            CreatePropertyReq(
                address="   ",
                property_type=PropertyTypeEnum.PRIVATE
            )


class TestPropertyRes:
    def test_valid_property_response(self):
        """Test creating a valid response model"""
        user_id = uuid4()
        neighbourhood_id = uuid4()
        now = datetime.now()

        model = PropertyRes(
            user_id=user_id,
            neighbourhood_id=neighbourhood_id,
            address="123 Main Street",
            property_type=PropertyTypeEnum.PRIVATE,
            created_at=now
        )
        assert model.user_id == user_id
        assert model.address == "123 Main Street"
        assert model.property_type == PropertyTypeEnum.PRIVATE

    def test_neighbourhood_id_optional(self):
        """Test that neighbourhood_id is optional"""
        user_id = uuid4()
        now = datetime.now()

        model = PropertyRes(
            user_id=user_id,
            neighbourhood_id=None,
            address="123 Main Street",
            property_type=PropertyTypeEnum.PUBLIC,
            created_at=now
        )
        assert model.neighbourhood_id is None

    def test_missing_required_field(self):
        """Test missing required fields"""
        with pytest.raises(ValidationError):
            PropertyRes(
                user_id=uuid4(),
                neighbourhood_id=uuid4(),
                address="123 Main Street"
                # Missing property_type and created_at
            )

    def test_empty_string_address(self):
        """Test that empty address raises ValidationError"""
        with pytest.raises(ValidationError):
            PropertyRes(
                user_id=uuid4(),
                neighbourhood_id=None,
                address="",
                property_type=PropertyTypeEnum.PRIVATE,
                created_at=datetime.now()
            )

    def test_whitespace_only_address(self):
        """Test that whitespace-only address is stripped and rejected"""
        with pytest.raises(ValidationError):
            PropertyRes(
                user_id=uuid4(),
                neighbourhood_id=None,
                address="   ",
                property_type=PropertyTypeEnum.PUBLIC,
                created_at=datetime.now()
            )


class TestCreatePropertyRes:
    def test_with_data(self):
        """Test response with data"""
        user_id = uuid4()
        neighbourhood_id = uuid4()
        now = datetime.now()

        data = PropertyRes(
            user_id=user_id,
            neighbourhood_id=neighbourhood_id,
            address="123 Main Street",
            property_type=PropertyTypeEnum.PRIVATE,
            created_at=now
        )
        model = CreatePropertyRes(
            status=201,
            message="Property created successfully",
            data=data
        )
        assert model.status == 201
        assert model.data.address == "123 Main Street"

    def test_with_none_fields(self):
        """Test response with optional None fields"""
        model = CreatePropertyRes(
            status=400
        )
        assert model.status == 400
        assert model.message is None
        assert model.data is None
