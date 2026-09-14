from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.camera import CameraVisibilityEnum
from app.models.property import PropertyTypeEnum
from app.schemas.property import InvitePropertyReq
from app.services import property_service as property_service_module
from app.services.property_service import (
    create_property_handler,
    get_user_properties_handler,
)

@pytest.fixture(autouse=True)
def mock_audit():
    with patch(
        "app.services.property_service.create_audit_log_item",
        new=AsyncMock(),
    ):
        yield

# create_property_handler tests
class TestCreateProperty:
    def setup_method(self):
        """Runs before each test method"""
        self.mock_db = Mock()
        self.mock_result = Mock()
        self.mock_db.execute = AsyncMock(return_value=self.mock_result)

        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.mock_result.scalar_one_or_none.return_value = self.mock_user

        self.mock_db.add = Mock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.flush = AsyncMock()
        self.mock_db.rollback = AsyncMock()

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
                self.mock_db,
                latitude=-26.2041,
                longitude=28.0473,
            )

            MockProperty.assert_called_once_with(
                address="100 Test Street",
                latitude=-26.2041,
                longitude=28.0473,
                property_type=PropertyTypeEnum.PRIVATE,
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
    async def test_no_user(self): #May be incorrect
        with patch('app.services.property_service.Property') as MockProperty, \
            patch('app.services.property_service.PropertyUser') as _MockPropertyUser:

            mock_prop = Mock()
            MockProperty.return_value = mock_prop
            self.mock_db.execute.return_value.scalar_one_or_none.return_value = None

            # expecting an exception bad req
            with pytest.raises(HTTPException) as exc_info:
                await create_property_handler(
                    "test 123",
                    PropertyTypeEnum.PRIVATE,
                    self.claims,
                    self.mock_db
                )
            assert exc_info.value.status_code == 404
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
        self.mock_result = Mock()
        self.mock_db.execute = AsyncMock(return_value=self.mock_result)

        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.mock_result.scalar_one_or_none.return_value = self.mock_user
        self.claims = {"sub": "cognito-sub-123"}

    @pytest.mark.asyncio
    async def test_happy_path_with_properties(self):
        """Test fetching properties when user has multiple properties"""

        self.mock_result.scalar_one_or_none.return_value = self.mock_user

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

        self.mock_result.scalars.return_value.all.return_value = [mock_prop1, mock_prop2]

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

    @pytest.mark.asyncio
    async def test_database_error_is_converted_to_http_500(self):
        self.mock_db.execute.side_effect = RuntimeError("database unavailable")

        with pytest.raises(HTTPException) as exc_info:
            await get_user_properties_handler(self.claims, self.mock_db)

        assert exc_info.value.status_code == 500
        assert "Failed to fetch properties" in exc_info.value.detail
        assert "database unavailable" in exc_info.value.detail


PROPERTY_ID = uuid4()
USER_ID = uuid4()
INVITED_USER_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()
CAMERA_ID = uuid4()


def _property_service_result(*, scalar=None, rows=None):
    result = Mock()
    result.scalar_one_or_none.return_value = scalar
    result.scalars.return_value.all.return_value = list(rows or [])
    result.all.return_value = list(rows or [])
    return result


def _property_service_db():
    db = Mock()
    db.execute = AsyncMock()
    db.add = Mock()
    db.delete = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


def _property_service_claims(
    *,
    cognito_sub="owner-cognito-sub",
    user_id=USER_ID,
):
    return {
        "sub": cognito_sub,
        "id": str(user_id),
    }


def _make_property():
    return SimpleNamespace(
        id=PROPERTY_ID,
        address="123 Test Street",
        property_type=PropertyTypeEnum.PRIVATE,
        latitude=-25.754,
        longitude=28.231,
        neighbourhood_id=NEIGHBOURHOOD_ID,
        created_at=datetime(2026, 1, 1),
    )


def _make_property_without_neighbourhood():
    property_obj = _make_property()
    property_obj.neighbourhood_id = None
    return property_obj


def _make_user(
    *,
    user_id=USER_ID,
    email="owner@example.com",
    first_name="Owner",
    last_name="User",
    cognito_sub="owner-cognito-sub",
):
    return SimpleNamespace(
        id=user_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        cognito_sub=cognito_sub,
    )


def _make_neighbourhood():
    return SimpleNamespace(
        id=NEIGHBOURHOOD_ID,
        name="Test Neighbourhood",
        location="Pretoria",
        join_code="ABC12345",
        created_at=datetime(2026, 1, 1),
    )


def _make_camera():
    return SimpleNamespace(
        id=CAMERA_ID,
        location="Front Gate",
        visibility=CameraVisibilityEnum.PUBLIC,
        created_at=datetime(2026, 1, 1),
    )


@pytest.mark.asyncio
async def test_create_property_rolls_back_on_integrity_error():
    db = _property_service_db()
    user = _make_user()

    db.execute.return_value = _property_service_result(
        scalar=user,
    )
    db.flush.side_effect = IntegrityError(
        "insert property",
        {},
        RuntimeError("duplicate property"),
    )

    claims = _property_service_claims()

    with patch(
        "app.services.property_service.create_audit_log_item",
        new=AsyncMock(),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await property_service_module.create_property_handler(
                addr="123 Test Street",
                prop_type=PropertyTypeEnum.PRIVATE,
                claims=claims,
                db=db,
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to add to property database"
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_property_details_returns_users_neighbourhood_and_cameras():
    db = _property_service_db()

    property_obj = _make_property()
    neighbourhood = _make_neighbourhood()
    owner = _make_user()
    camera = _make_camera()

    property_user = SimpleNamespace(
        user=owner,
        user_id=USER_ID,
        property_id=PROPERTY_ID,
        is_admin=True,
    )

    db.execute.side_effect = [
        _property_service_result(scalar=property_obj),
        _property_service_result(rows=[property_user]),
        _property_service_result(scalar=neighbourhood),
        _property_service_result(rows=[camera]),
    ]

    claims = {
        "sub": "owner-cognito-sub",
        "custom:role": "RESIDENT",
    }

    with patch(
        "app.services.property_service.is_property_member",
        new=AsyncMock(return_value=True),
    ) as is_member:
        response = await property_service_module.get_property_details_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=claims,
        )

    is_member.assert_awaited_once_with(
        PROPERTY_ID,
        claims,
        db,
    )

    assert response["property_id"] == PROPERTY_ID
    assert response["address"] == "123 Test Street"
    assert response["property_type"] == PropertyTypeEnum.PRIVATE.value
    assert response["latitude"] == -25.754
    assert response["longitude"] == 28.231

    assert response["users"] == [
        {
            "id": USER_ID,
            "email": "owner@example.com",
            "first_name": "Owner",
            "last_name": "User",
        }
    ]

    assert response["neighbourhood"] == {
        "id": NEIGHBOURHOOD_ID,
        "name": "Test Neighbourhood",
        "location": "Pretoria",
        "join_code": "ABC12345",
        "created_at": datetime(2026, 1, 1),
    }

    assert response["cameras"] == [
        {
            "id": CAMERA_ID,
            "location": "Front Gate",
            "visibility": CameraVisibilityEnum.PUBLIC.value,
            "created_at": datetime(2026, 1, 1),
        }
    ]


@pytest.mark.asyncio
async def test_get_property_details_returns_none_neighbourhood_when_unlinked():
    db = _property_service_db()

    property_obj = _make_property_without_neighbourhood()
    db.execute.side_effect = [
        _property_service_result(scalar=property_obj),
        _property_service_result(rows=[]),
        _property_service_result(rows=[]),
    ]

    claims = {
        "sub": "owner-cognito-sub",
        "custom:role": "SYSTEM_ADMIN",
    }

    with patch(
        "app.services.property_service.is_property_member",
        new=AsyncMock(return_value=False),
    ):
        response = await property_service_module.get_property_details_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=claims,
        )

    assert response["property_id"] == PROPERTY_ID
    assert response["neighbourhood"] is None
    assert response["users"] == []
    assert response["cameras"] == []


@pytest.mark.asyncio
async def test_get_property_details_rejects_user_without_access():
    db = _property_service_db()
    claims = {
        "sub": "owner-cognito-sub",
        "custom:role": "RESIDENT",
    }

    with patch(
        "app.services.property_service.is_property_member",
        new=AsyncMock(return_value=False),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await property_service_module.get_property_details_handler(
                property_id=PROPERTY_ID,
                db=db,
                claims=claims,
            )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "You do not have permission to view this property."
    )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_property_details_returns_404_when_property_does_not_exist():
    db = _property_service_db()
    db.execute.return_value = _property_service_result(scalar=None)

    claims = {
        "sub": "owner-cognito-sub",
        "custom:role": "RESIDENT",
    }

    with patch(
        "app.services.property_service.is_property_member",
        new=AsyncMock(return_value=True),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await property_service_module.get_property_details_handler(
                property_id=PROPERTY_ID,
                db=db,
                claims=claims,
            )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Property not found."


@pytest.mark.asyncio
async def test_get_property_members_returns_members():
    db = _property_service_db()

    owner = _make_user()
    invited_user = _make_user(
        user_id=INVITED_USER_ID,
        email="member@example.com",
        first_name="Member",
        last_name="User",
        cognito_sub="member-cognito-sub",
    )

    db.execute.side_effect = [
        _property_service_result(scalar=owner),
        _property_service_result(
            rows=[
                (owner, True),
                (invited_user, False),
            ]
        ),
    ]

    response = await property_service_module.get_property_members_handler(
        property_id=PROPERTY_ID,
        db=db,
        claims=_property_service_claims(),
    )

    assert len(response.members) == 2

    assert response.members[0].user_id == USER_ID
    assert response.members[0].first_name == "Owner"
    assert response.members[0].is_admin is True

    assert response.members[1].user_id == INVITED_USER_ID
    assert response.members[1].email == "member@example.com"
    assert response.members[1].is_admin is False


@pytest.mark.asyncio
async def test_get_property_members_rejects_missing_user():
    db = _property_service_db()
    db.execute.return_value = _property_service_result(scalar=None)

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.get_property_members_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_get_property_members_returns_empty_members_list():
    db = _property_service_db()

    db.execute.side_effect = [
        _property_service_result(scalar=_make_user()),
        _property_service_result(rows=[]),
    ]

    response = await property_service_module.get_property_members_handler(
        property_id=PROPERTY_ID,
        db=db,
        claims=_property_service_claims(),
    )

    assert response.members == []


@pytest.mark.asyncio
async def test_invite_property_member_returns_email_sent_true():
    db = _property_service_db()

    inviter = _make_user()
    property_obj = _make_property()
    invited_user = _make_user(
        user_id=INVITED_USER_ID,
        email="new-member@example.com",
        first_name="New",
        last_name="Member",
        cognito_sub="new-member-sub",
    )

    db.execute.side_effect = [
        _property_service_result(scalar=inviter),
        _property_service_result(scalar=property_obj),
        _property_service_result(scalar=invited_user),
        _property_service_result(scalar=None),
    ]

    request = InvitePropertyReq(
        email="new-member@example.com",
    )

    with patch(
        "app.services.property_service.asyncio.to_thread",
        new=AsyncMock(return_value=(True, None)),
    ) as send_email:
        response = await property_service_module.invite_property_member_handler(
            req=request,
            property_id=PROPERTY_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert response == {
        "message": "Property member invited successfully",
        "email_sent": True,
    }

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    send_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_invite_property_member_handles_email_failure():
    db = _property_service_db()

    inviter = _make_user()
    property_obj = _make_property()
    invited_user = _make_user(
        user_id=INVITED_USER_ID,
        email="new-member@example.com",
        first_name="New",
        last_name="Member",
        cognito_sub="new-member-sub",
    )

    db.execute.side_effect = [
        _property_service_result(scalar=inviter),
        _property_service_result(scalar=property_obj),
        _property_service_result(scalar=invited_user),
        _property_service_result(scalar=None),
    ]

    request = InvitePropertyReq(
        email="new-member@example.com",
    )

    with patch(
        "app.services.property_service.asyncio.to_thread",
        new=AsyncMock(return_value=(False, "SMTP unavailable")),
    ):
        response = await property_service_module.invite_property_member_handler(
            req=request,
            property_id=PROPERTY_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert response == {
        "message": "Property member invited successfully",
        "email_sent": False,
    }
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_invite_property_member_rejects_unknown_invited_user():
    db = _property_service_db()

    db.execute.side_effect = [
        _property_service_result(scalar=_make_user()),
        _property_service_result(scalar=_make_property()),
        _property_service_result(scalar=None),
    ]

    request = InvitePropertyReq(
        email="missing@example.com",
    )

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.invite_property_member_handler(
            req=request,
            property_id=PROPERTY_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == (
        "User with that email does not exist"
    )
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_invite_property_member_rejects_existing_member():
    db = _property_service_db()

    inviter = _make_user()
    property_obj = _make_property()
    invited_user = _make_user(
        user_id=INVITED_USER_ID,
        email="existing@example.com",
        first_name="Existing",
        last_name="Member",
    )
    existing_member = SimpleNamespace(
        property_id=PROPERTY_ID,
        user_id=INVITED_USER_ID,
        is_admin=False,
    )

    db.execute.side_effect = [
        _property_service_result(scalar=inviter),
        _property_service_result(scalar=property_obj),
        _property_service_result(scalar=invited_user),
        _property_service_result(scalar=existing_member),
    ]

    request = InvitePropertyReq(
        email="existing@example.com",
    )

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.invite_property_member_handler(
            req=request,
            property_id=PROPERTY_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == (
        "User is already a property member"
    )
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_property_member_deletes_non_admin_member():
    db = _property_service_db()

    membership = SimpleNamespace(
        property_id=PROPERTY_ID,
        user_id=INVITED_USER_ID,
        is_admin=False,
    )

    db.execute.side_effect = [
        _property_service_result(scalar=membership),
        Mock(),
    ]

    response = await property_service_module.remove_property_member_handler(
        property_id=PROPERTY_ID,
        user_id=INVITED_USER_ID,
        db=db,
        claims=_property_service_claims(),
    )

    assert response is None
    assert db.execute.await_count == 2
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_property_member_allows_admin_removal_when_another_admin_exists():
    db = _property_service_db()

    membership = SimpleNamespace(
        property_id=PROPERTY_ID,
        user_id=INVITED_USER_ID,
        is_admin=True,
    )
    another_admin = SimpleNamespace(
        property_id=PROPERTY_ID,
        user_id=USER_ID,
        is_admin=True,
    )

    db.execute.side_effect = [
        _property_service_result(scalar=membership),
        _property_service_result(rows=[membership, another_admin]),
        Mock(),
    ]

    response = await property_service_module.remove_property_member_handler(
        property_id=PROPERTY_ID,
        user_id=INVITED_USER_ID,
        db=db,
        claims=_property_service_claims(),
    )

    assert response is None
    assert db.execute.await_count == 3
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_property_member_rejects_last_admin():
    db = _property_service_db()

    membership = SimpleNamespace(
        property_id=PROPERTY_ID,
        user_id=INVITED_USER_ID,
        is_admin=True,
    )

    db.execute.side_effect = [
        _property_service_result(scalar=membership),
        _property_service_result(rows=[membership]),
    ]

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.remove_property_member_handler(
            property_id=PROPERTY_ID,
            user_id=INVITED_USER_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == (
        "The last property administrator cannot be removed"
    )
    db.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_get_property_details_rejects_missing_property_id():
    db = _property_service_db()

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.get_property_details_handler(
            property_id=None,
            db=db,
            claims={"custom:role": "SYSTEM_ADMIN"},
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No property ID provided."


@pytest.mark.asyncio
async def test_get_property_details_converts_unexpected_error():
    db = _property_service_db()
    db.execute.side_effect = RuntimeError("database unavailable")

    with patch(
        "app.services.property_service.is_property_member",
        new=AsyncMock(return_value=True),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await property_service_module.get_property_details_handler(
                property_id=PROPERTY_ID,
                db=db,
                claims={"custom:role": "RESIDENT"},
            )

    assert exc_info.value.status_code == 500
    assert "Failed to fetch property details" in exc_info.value.detail
    assert "database unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_property_members_requires_claims():
    db = _property_service_db()

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.get_property_members_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_get_property_members_converts_unexpected_error():
    db = _property_service_db()
    db.execute.side_effect = RuntimeError("database unavailable")

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.get_property_members_handler(
            property_id=PROPERTY_ID,
            db=db,
            claims={"sub": "owner-cognito-sub"},
        )

    assert exc_info.value.status_code == 500
    assert "Failed to fetch members" in exc_info.value.detail


@pytest.mark.asyncio
async def test_invite_property_member_requires_claims():
    db = _property_service_db()

    request = InvitePropertyReq(
        email="member@example.com",
    )

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.invite_property_member_handler(
            req=request,
            property_id=PROPERTY_ID,
            db=db,
            claims=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_invite_property_member_rejects_missing_inviter():
    db = _property_service_db()
    db.execute.return_value = _property_service_result(scalar=None)

    request = InvitePropertyReq(
        email="member@example.com",
    )

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.invite_property_member_handler(
            req=request,
            property_id=PROPERTY_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Inviting user not found"


@pytest.mark.asyncio
async def test_invite_property_member_rejects_missing_property():
    db = _property_service_db()

    db.execute.side_effect = [
        _property_service_result(scalar=_make_user()),
        _property_service_result(scalar=None),
    ]

    request = InvitePropertyReq(
        email="member@example.com",
    )

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.invite_property_member_handler(
            req=request,
            property_id=PROPERTY_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Property not found"


@pytest.mark.asyncio
async def test_invite_property_member_rolls_back_on_unexpected_error():
    db = _property_service_db()

    inviter = _make_user()
    property_obj = _make_property()
    invited_user = _make_user(
        user_id=INVITED_USER_ID,
        email="member@example.com",
        first_name="Member",
        last_name="User",
    )

    db.execute.side_effect = [
        _property_service_result(scalar=inviter),
        _property_service_result(scalar=property_obj),
        _property_service_result(scalar=invited_user),
        _property_service_result(scalar=None),
    ]
    db.commit.side_effect = RuntimeError("database unavailable")

    request = InvitePropertyReq(
        email="member@example.com",
    )

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.invite_property_member_handler(
            req=request,
            property_id=PROPERTY_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert exc_info.value.status_code == 500
    assert "Failed to invite property member" in exc_info.value.detail
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_property_member_requires_claims():
    db = _property_service_db()

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.remove_property_member_handler(
            property_id=PROPERTY_ID,
            user_id=INVITED_USER_ID,
            db=db,
            claims=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_remove_property_member_rejects_missing_membership():
    db = _property_service_db()
    db.execute.return_value = _property_service_result(scalar=None)

    with pytest.raises(HTTPException) as exc_info:
        await property_service_module.remove_property_member_handler(
            property_id=PROPERTY_ID,
            user_id=INVITED_USER_ID,
            db=db,
            claims=_property_service_claims(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == (
        "User is not a member of this property"
    )
    db.commit.assert_not_awaited()