from pydantic import ValidationError
import pytest
from uuid import uuid4
from app.schemas.neighbourhood import CreateNeighbourhoodReq, NeighbourhoodRes, CreateNeighbourhoodRes
from datetime import datetime

class TestCreateNeighbourhoodReq:
    def test_valid_model(self):
        """Happy path"""
        name = "Downtown"
        location = "Pretoria"
        property_id = uuid4()

        req = CreateNeighbourhoodReq(
            name = name,
            location = location,
            property_id = property_id
        )

        assert req.name == name
        assert req.location == location
        assert req.property_id == property_id

    def test_missing_name(self):
        """Test that name as none raises an error"""
        location = "Pretoria"
        property_id = uuid4()
        with pytest.raises(ValidationError):
            CreateNeighbourhoodReq(
                name = None,
                location = location,
                property_id = property_id
            )
        
    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError"""
        with pytest.raises(ValidationError):
            CreateNeighbourhoodReq(
                name="Downtown District",
                location="Main Street"
                # Missing property_id
            )

    def test_invalid_uuid_type(self):
        """Test that invalid UUID raises ValidationError"""
        with pytest.raises(ValidationError):
            CreateNeighbourhoodReq(
                name="Downtown District",
                location="Main Street",
                property_id="not-a-uuid" 
            )

    def test_empty_string_name(self):
        """Test that empty name raises ValidationError"""
        property_id = uuid4()
        with pytest.raises(ValidationError):
            CreateNeighbourhoodReq(
                name="",
                location="Main Street",
                property_id=property_id
            )

    def test_empty_string_location(self):
        """Test that empty location raises ValidationError"""
        property_id = uuid4()
        with pytest.raises(ValidationError):
            CreateNeighbourhoodReq(
                name="Downtown District",
                location="",
                property_id=property_id
            )

    def test_whitespace_only_string(self):
        """Test that whitespace-only strings are stripped and rejected"""
        property_id = uuid4()
        with pytest.raises(ValidationError):
            CreateNeighbourhoodReq(
                name="   ",
                location="Main Street",
                property_id=property_id
            )


class TestNeighbourhoodRes:
    def test_valid_neighbourhood_response(self):
        """Test creating a valid response model"""
        neighbourhood_id = uuid4()
        now = datetime.now()
        model = NeighbourhoodRes(
            id=neighbourhood_id,
            name="Downtown District",
            location="Main Street",
            join_code="ABC123",
            created_at=now
        )
        assert model.id == neighbourhood_id
        assert model.name == "Downtown District"

    def test_missing_required_field(self):
        """Test missing required fields"""
        with pytest.raises(ValidationError):
            NeighbourhoodRes(
                id=uuid4(),
                name="Downtown District",
                location="Main Street"
                # Missing join_code and created_at
            )

class TestCreateNeighbourhoodRes:
    def test_with_data(self):
        """Test response with data"""
        neighbourhood_id = uuid4()
        now = datetime.now()
        data = NeighbourhoodRes(
            id=neighbourhood_id,
            name="Downtown District",
            location="Main Street",
            join_code="ABC123",
            created_at=now
        )
        model = CreateNeighbourhoodRes(
            status=201,
            message="Created successfully",
            data=data
        )
        assert model.status == 201
        assert model.data.name == "Downtown District"

    def test_with_none_fields(self):
        """Test response with optional None fields"""
        model = CreateNeighbourhoodRes(
            status=400
        )
        assert model.status == 400
        assert model.message is None
        assert model.data is None