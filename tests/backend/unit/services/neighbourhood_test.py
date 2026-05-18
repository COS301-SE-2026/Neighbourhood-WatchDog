import pytest, pytest_asyncio
from unittest.mock import Mock
from uuid import uuid4

class TestCreateNeighbourhood:
    def setup_method(self):
        self.mock_db = Mock()

        #mock the property 
        self.mock_property = Mock()
        self.mock_property.id = uuid4()

        #mock the prop user 
        self.mock_property_user = Mock()
        self.mock_property_user.property_id = uuid4
        self.mock_property_user.property_id = Mock()
        self.mock_property_user.user.cognito_sub = "cognito-sub-123"

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
        with patch('app.services.neighbourhood_servie.Neighbourhoood') as MockNeighbourhood, \
        patch('app.services.neighbourhood_service.PropertyUser') as MockPropertyUser:
            
            mock_prop = Mock()