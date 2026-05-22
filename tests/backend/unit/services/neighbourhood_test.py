import pytest
from fastapi import HTTPException
from unittest.mock import Mock
from app.services.neighbourhood_service import create_neighbourhood_handler
from uuid import uuid4
from datetime import datetime

class TestCreateNeighbourhood:
    def setup_method(self):
        self.mock_db = Mock()

        #mock the property
        self.mock_property = Mock()
        self.mock_property.id = uuid4()
        self.mock_property.neighbourhood_id = None

        #mock the prop user 
        self.mock_property_user = Mock()
        self.mock_property_user.property_id = uuid4()
        self.mock_property_user.user = Mock()
        self.mock_property_user.user.cognito_sub = "cognito-sub-123"

        #mock the neighbourhood
        self.mock_neighbourhood = Mock()
        self.mock_neighbourhood.id = uuid4()
        self.mock_neighbourhood.name = "Test name fr"
        self.mock_neighbourhood.location = "Second lo"
        self.mock_neighbourhood.join_code = "ABC12345"
        self.mock_neighbourhood.created_at = datetime.now()

        # mockin da queries
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            None,  # join_code uniqueness check
            self.mock_property,
            self.mock_property_user
        ]

        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.rollback = Mock()

        # Mock db.refresh to set id and created_at on the neighbourhood object
        def mock_refresh(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = uuid4()
            if hasattr(obj, 'created_at') and obj.created_at is None:
                obj.created_at = datetime.now()

        self.mock_db.refresh = Mock(side_effect=mock_refresh)

        self.claims = {"sub": "cognito-sub-123"}

    @pytest.mark.asyncio
    async def test_happy_path(self):
        neighbourhood = await create_neighbourhood_handler(
            name = "Test name",
            location = "second location",
            property_id = uuid4(),
            db = self.mock_db,
            claims = self.claims,
        )

        assert neighbourhood is not None
        assert neighbourhood.name == "Test name"
        assert neighbourhood.location == "second location"
        assert neighbourhood.join_code is not None

        assert self.mock_db.add.call_count == 1
        assert self.mock_db.flush.call_count == 2
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_no_name_entered(self):
        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "",
                location = "second location",
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

        assert exception.value.status_code == 400

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_name_none(self):
        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = None,
                location = "second location",
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

        assert exception.value.status_code == 400

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0
    
    @pytest.mark.asyncio
    async def test_empty_location(self):
        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "Name",
                location = "",
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

        assert exception.value.status_code == 400
        assert exception.value.detail == "No neighbourhood locationation given"

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_location_none(self):
        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "Name",
                location = None,
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

        assert exception.value.status_code == 400
        assert exception.value.detail == "No neighbourhood locationation given"

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_no_property_id(self):
        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "Name",
                location = "Second lo",
                property_id = None,
                db = self.mock_db,
                claims = self.claims,
            )

        assert exception.value.status_code == 400
        assert exception.value.detail == "No property id given to link the neighbourhood to"

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_no_claims(self):
        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "Name",
                location = "Second lo",
                property_id = uuid4(),
                db = self.mock_db,
                claims = None,
            )

        assert exception.value.status_code == 401
        assert exception.value.detail == "Not authenticated"

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_db_none(self):
        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "Name",
                location = "Location",
                property_id = uuid4(),
                db = None,
                claims = self.claims,
            )

        assert exception.value.status_code == 500
        assert exception.value.detail == "No database session"

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_property_not_found(self):
        #overriding it coz it's not a parameter directly passed into the function
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            None,  # join_code uniqueness check
            None,  # Property not found
            self.mock_property_user
        ]

        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "Name",
                location = "Location",
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

        assert exception.value.status_code == 404
        assert exception.value.detail == "Property not found"

        assert self.mock_db.add.call_count == 1
        assert self.mock_db.flush.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 1

    @pytest.mark.asyncio
    async def test_prop_user_not_found(self):
        #we overriding it again for the same reason as above
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            None,  # join_code uniqueness check
            self.mock_property,
            None  # PropertyUser not found
        ]

        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "Name",
                location = "Location",
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

        assert exception.value.status_code == 403
        assert exception.value.detail == "User does not have access to this property"

        assert self.mock_db.add.call_count == 1
        assert self.mock_db.flush.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 1

    @pytest.mark.asyncio
    async def test_cognito_sub_mismatch(self):
        #we overriding it again for the same reason as above
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            None,  # join_code uniqueness check
            self.mock_property,
            self.mock_property_user  # PropertyUser found but cognito_sub doesn't match
        ]

        self.claims = {"sub": "cognito-sub"}

        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name = "Name",
                location = "Location",
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

        assert exception.value.status_code == 403
        assert exception.value.detail == "This user does not live in the property they are trying to add to the neighbourhood they are creating"

        assert self.mock_db.add.call_count == 1
        assert self.mock_db.flush.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 1