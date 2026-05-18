from pydantic import ValidationError
import pytest
from uuid import uuid4
from app.schemas.neighbourhood import CreateNeighbourhoodReq, NeighbourhoodRes, CreateNeighbourhoodRes

class TestCreateNeighbourhoodReq:
    def test_valid_model(self):
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

        location = "Pretoria"
        property_id = uuid4()
        with pytest.raises(ValidationError):
            CreateNeighbourhoodReq(
                name = None,
                location = location,
                property_id = property_id
            )