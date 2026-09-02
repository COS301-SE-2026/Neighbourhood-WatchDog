import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, Mock, AsyncMock, patch
from app.services.neighbourhood_service import create_neighbourhood_handler, get_neighbourhood_members_handler
from app.models.neighbourhood_user import NeighbourhoodUser, NeighbourhoodRole
from uuid import uuid4
from datetime import datetime
from app.models.neighbourhood import Neighbourhood

AUDIT_PATCH = "app.services.neighbourhood_service.create_audit_log_item"

@pytest.fixture(autouse=True)
def mock_audit():
    with patch(
        "app.services.neighbourhood_service.create_audit_log_item",
        new=AsyncMock(),
    ):
        yield

TEST_NEIGHBOURHOOD_NAME = "Test name"

def make_mock_db():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = Mock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.refresh = AsyncMock()
    return mock_db, mock_result

def make_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_rows_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


class TestCreateNeighbourhood:
    def setup_method(self):
        self.mock_db, self.mock_result = make_mock_db()

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

        #mock creator user
        self.mock_creator = Mock()
        self.mock_creator.id = uuid4()
        self.mock_creator.cognito_sub = "cognito-sub-123"

        # mockin da queries
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_property,
            self.mock_property_user,
            self.mock_creator,
            None,  # join_code uniqueness check
        ]

        def mock_add(obj):
            if isinstance(obj, Neighbourhood):
                obj.id = uuid4()
                obj.created_at = datetime.now()

        self.mock_db.add = Mock(side_effect=mock_add)

        # Mock db.refresh to set id and created_at on the neighbourhood object
        def mock_refresh(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = uuid4()
            if hasattr(obj, 'created_at') and obj.created_at is None:
                obj.created_at = datetime.now()

        self.mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        self.claims = {
            "id": str(uuid4()),
            "sub": "cognito-sub-123",
        }

    def _added_neighbourhood_users(self):
        """Returns every NeighbourhoodUser instance passed to db.add()"""
        return [
            call.args[0]
            for call in self.mock_db.add.call_args_list
            if call.args and isinstance(call.args[0], NeighbourhoodUser)
        ]

    @pytest.mark.asyncio
    async def test_happy_path(self):
        neighbourhood = await create_neighbourhood_handler(
            name = TEST_NEIGHBOURHOOD_NAME,
            location = "second location",
            property_id = uuid4(),
            db = self.mock_db,
            claims = self.claims,
        )

        assert neighbourhood is not None
        assert neighbourhood.name == TEST_NEIGHBOURHOOD_NAME
        assert neighbourhood.location == "second location"
        assert neighbourhood.join_code is not None

        assert self.mock_db.add.call_count == 2
        assert self.mock_db.flush.call_count == 1
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
        assert exception.value.detail == "No neighbourhood location given"

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
        assert exception.value.detail == "No neighbourhood location given"

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
            None,  # Property not found
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

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 1

    @pytest.mark.asyncio
    async def test_prop_user_not_found(self):
        #we overriding it again for the same reason as above
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_property,
            None  # PropertyUser not found. caller doesnt own the property
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
        assert exception.value.detail == "You do not own this property"

        assert self.mock_db.add.call_count == 0
        assert self.mock_db.flush.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 1

    @pytest.mark.asyncio
    async def test_creator_gets_neighbourhood_admin_membership(self):
        neighbourhood = await create_neighbourhood_handler(
            name=TEST_NEIGHBOURHOOD_NAME,
            location="second location",
            property_id=uuid4(),
            db=self.mock_db,
            claims=self.claims,
        )

        added_memberships = self._added_neighbourhood_users()
        assert len(added_memberships) == 1

        membership = added_memberships[0]
        assert membership.user_id == self.mock_creator.id
        assert membership.role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
        assert membership.neighbourhood_id == neighbourhood.id   
    
    @pytest.mark.asyncio
    async def test_creator_not_found_in_db_raises_401(self):
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_property,
            self.mock_property_user,
            None, # creator lookup returns nothing
        ]

        with pytest.raises(HTTPException) as exception:
            await create_neighbourhood_handler(
                name="Name",
                location="Location",
                property_id=uuid4(),
                db=self.mock_db,
                claims=self.claims,
            )

        assert exception.value.status_code == 401
        assert exception.value.detail == "Authenticated user not found in database"
        
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 1

    @pytest.mark.asyncio
    async def test_two_neighbourhoods_have_distinct_join_codes(self):
        mock_db_2, mock_result_2 = make_mock_db()
 
        mock_property_2 = Mock()
        mock_property_2.id = uuid4()
        mock_property_2.neighbourhood_id = None
 
        mock_property_user_2 = Mock()
        mock_property_user_2.property_id = uuid4()
        mock_property_user_2.user = Mock()
        mock_property_user_2.user.cognito_sub = "cognito-sub-123"
 
        mock_creator_2 = Mock()
        mock_creator_2.id = uuid4()
        mock_creator_2.cognito_sub = "cognito-sub-123"
 
        mock_db_2.execute.return_value.scalar_one_or_none.side_effect = [
            mock_property_2,
            mock_property_user_2,
            mock_creator_2,
            None,               # join_code uniqueness check
        ]
        
        def mock_add_2(obj):
            if isinstance(obj, Neighbourhood):
                obj.id = uuid4()
                obj.created_at = datetime.now()

        mock_db_2.add = Mock(side_effect=mock_add_2)
 
        def mock_refresh_2(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = uuid4()
            if hasattr(obj, 'created_at') and obj.created_at is None:
                obj.created_at = datetime.now()
 
        mock_db_2.refresh = AsyncMock(side_effect=mock_refresh_2)
 
        nb1 = await create_neighbourhood_handler(
            name="Neighbourhood One",
            location="Location One",
            property_id=uuid4(),
            db=self.mock_db,
            claims=self.claims,
        )
 
        nb2 = await create_neighbourhood_handler(
            name="Neighbourhood Two",
            location="Location Two",
            property_id=uuid4(),
            db=mock_db_2,
            claims=self.claims,
        )
 
        assert nb1.join_code != nb2.join_code


class TestGetNeighbourhoodMembers:

    @pytest.mark.asyncio
    async def test_admin_can_view_neighbourhood_members(self):
        mock_db = AsyncMock()

        neighbourhood_id = uuid4()
        admin_id = uuid4()
        member_id = uuid4()

        neighbourhood = Mock()
        neighbourhood.id = neighbourhood_id

        admin_membership = Mock()
        admin_membership.user_id = admin_id
        admin_membership.neighbourhood_id = neighbourhood_id
        admin_membership.role = (
            NeighbourhoodRole.NEIGHBOURHOOD_ADMIN
        )

        member_membership = Mock()
        member_membership.user_id = member_id
        member_membership.neighbourhood_id = neighbourhood_id
        member_membership.role = NeighbourhoodRole.RESIDENT

        member_user = Mock()
        member_user.id = member_id
        member_user.first_name = "Test"
        member_user.last_name = "Resident"
        member_user.email = "resident@example.com"

        mock_db.execute = AsyncMock(
            side_effect=[
                make_scalar_result(neighbourhood),
                make_scalar_result(admin_membership),
                make_rows_result(
                    [(member_membership, member_user)]
                )
            ]
        )

        result = await get_neighbourhood_members_handler(
            neighbourhood_id=neighbourhood_id,
            db=mock_db,
            claims={"id": str(admin_id)}
        )

        assert len(result) == 1
        assert result[0].user_id == member_id
        assert result[0].first_name == "Test"
        assert result[0].last_name == "Resident"
        assert result[0].email == "resident@example.com"
        assert result[0].role == NeighbourhoodRole.RESIDENT

        assert mock_db.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_non_admin_cannot_view_neighbourhood_members(self):
        mock_db = AsyncMock()

        neighbourhood_id = uuid4()
        user_id = uuid4()

        neighbourhood = Mock()
        neighbourhood.id = neighbourhood_id

        mock_db.execute = AsyncMock(
            side_effect=[
                make_scalar_result(neighbourhood),
                make_scalar_result(None),
            ]
        )

        with pytest.raises(HTTPException) as exception:
            await get_neighbourhood_members_handler(
                neighbourhood_id=neighbourhood_id,
                db=mock_db,
                claims={"id": str(user_id)},
            )

        assert exception.value.status_code == 403
        assert (
            exception.value.detail == "Only neighbourhood admins can view members"
        )