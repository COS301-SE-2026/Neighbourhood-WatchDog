from pydantic import ValidationError
import pytest
from uuid import uuid4
from app.schemas.neighbourhood import CreateNeighbourhoodReq, NeighbourhoodRes, CreateNeighbourhoodRes, UpdateSecurityAvailabilityRes, UpdateSecurityAvailabilityReq
from app.models.security_officer import AvailabilityStatus
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

class TestUpdateSecurityAvailabilityReq:
    def test_valid_model(self):
        """Happy path"""
        neighbourhood_id = uuid4()

        req = UpdateSecurityAvailabilityReq(
            neighbourhood_id=neighbourhood_id,
            new_availability=AvailabilityStatus.AVAILABLE,
        )

        assert req.neighbourhood_id == neighbourhood_id
        assert req.new_availability == AvailabilityStatus.AVAILABLE

    def test_accepts_string_enum(self):
        """Raw string values should be accepted since Availability is a string enum"""
        req = UpdateSecurityAvailabilityReq(
                neighbourhood_id=uuid4(),
                new_availability="BUSY",
            )

        assert req.new_availability == AvailabilityStatus.BUSY

    def test_missing_neighbourhood_id_raises(self):
        """Test missing neighbourhood id raises validationError"""
        with pytest.raises(ValidationError):
            UpdateSecurityAvailabilityReq(
                new_availability=AvailabilityStatus.AVAILABLE,
            )

    def test_missing_availability_raises(self):
        """Test missing new availability raises validationError"""
        with pytest.raises(ValidationError):
            UpdateSecurityAvailabilityReq(
                neighbourhood_id=uuid4(),
            )

    def test_invalid_uuid_type(self):
        "Test invalid neighbourhood_id raises"
        with pytest.raises(ValidationError):
            UpdateSecurityAvailabilityReq(
                neighbourhood_id="not-a-uuid",
                new_availability=AvailabilityStatus.AVAILABLE,
            )

    def test_invalid_availability_value(self):
        "Test invalid availability raises"
        with pytest.raises(ValidationError):
            UpdateSecurityAvailabilityReq(
                neighbourhood_id=uuid4(),
                new_availability="ON_A_BREAK",
            )

    def test_none_availability_value(self):
        "Test None is rejected"
        with pytest.raises(ValidationError):
            UpdateSecurityAvailabilityReq(
                neighbourhood_id=uuid4(),
                new_availability=None,
            )

class TestUpdateSecurityAvailabilityRes:
    def test_with_message(self):
        """Test response with a message"""
        model = UpdateSecurityAvailabilityRes(
            status=200,
            message="Availability status updated sucessfully",
        )
        assert model.status == 200
        assert model.message == "Availability status updated sucessfully"

    def test_without_message(self):
        """Test response without optional message"""
        model = UpdateSecurityAvailabilityRes(status=200)
        assert model.status == 200
        assert model.message is None

    def test_missing_status(self):
        """Test that missing status raises error"""
        with pytest.raises(ValidationError):
            UpdateSecurityAvailabilityRes(
                 message="Availability status updated sucessfully"
            )