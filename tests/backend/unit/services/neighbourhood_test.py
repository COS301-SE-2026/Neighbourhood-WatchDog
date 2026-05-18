import pytest, pytest_asyncio
from fastapi import HTTPException
from unittest.mock import Mock, patch
from app.services.neighbourhood_service import create_neighbourhood_handler
from uuid import uuid4
from datetime import datetime

class TestCreateNeighbourhood:
    def setup_method(self):
        self.mock_db = Mock()

        #mock the property 
        self.mock_property = Mock()
        self.mock_property.id = uuid4()

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
        self.mock_neighbourhood.created_at = datetime.now()

        # mockin da queries
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_property,
            self.mock_property_user
        ]

        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.rollback = Mock()

        self.claims = {"sub": "cognito-sub-123"}

    @pytest.mark.asyncio
    async def test_happy_path(self):
        with patch('app.services.neighbourhood_service.Neighbourhood') as MockNeighbourhood:
            
            MockNeighbourhood.return_value = self.mock_neighbourhood

            neighbourhood = await create_neighbourhood_handler(
                name = "Test name",
                location = "second location",
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

            assert neighbourhood is not None
            assert neighbourhood.id == self.mock_neighbourhood.id
            assert neighbourhood.name == self.mock_neighbourhood.name

            assert self.mock_db.add.call_count == 1
            assert self.mock_db.flush.call_count == 2
            assert self.mock_db.commit.call_count == 1
            assert self.mock_db.refresh.call_count == 1
            assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_happy_path(self):
        with patch('app.services.neighbourhood_service.Neighbourhood') as MockNeighbourhood:
            
            MockNeighbourhood.return_value = self.mock_neighbourhood

            neighbourhood = await create_neighbourhood_handler(
                name = "Test name",
                location = "second location",
                property_id = uuid4(),
                db = self.mock_db,
                claims = self.claims,
            )

            assert neighbourhood is not None
            assert neighbourhood.id == self.mock_neighbourhood.id
            assert neighbourhood.name == self.mock_neighbourhood.name

            assert self.mock_db.add.call_count == 1
            assert self.mock_db.flush.call_count == 2
            assert self.mock_db.commit.call_count == 1
            assert self.mock_db.refresh.call_count == 1
            assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_no_name_entered(self):
        with patch('app.services.neighbourhood_service.Neighbourhood') as MockNeighbourhood:
            
            MockNeighbourhood.return_value = self.mock_neighbourhood

            with pytest.raises(HTTPException) as exception:
                await create_neighbourhood_handler(
                    name = "",
                    location = "second location",
                    property_id = uuid4(),
                    db = self.mock_db,
                    claims = self.claims,
                )

            assert exception.value == 400

            assert self.mock_db.add.call_count == 0
            assert self.mock_db.flush.call_count == 0
            assert self.mock_db.commit.call_count == 0
            assert self.mock_db.refresh.call_count == 0
            assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_name_none(self):
        with patch('app.services.neighbourhood_service.Neighbourhood') as MockNeighbourhood:
            
            MockNeighbourhood.return_value = self.mock_neighbourhood

            with pytest.raises(HTTPException) as exception:
                await create_neighbourhood_handler(
                    name = None,
                    location = "second location",
                    property_id = uuid4(),
                    db = self.mock_db,
                    claims = self.claims,
                )

            assert exception.value == 400

            assert self.mock_db.add.call_count == 0
            assert self.mock_db.flush.call_count == 0
            assert self.mock_db.commit.call_count == 0
            assert self.mock_db.refresh.call_count == 0
            assert self.mock_db.rollback.call_count == 0