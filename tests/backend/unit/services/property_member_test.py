from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.property import InvitePropertyReq
from app.services import property_service as service


CLAIMS = {"sub": "inviter-cognito-sub"}
PROPERTY_ID = uuid4()
INVITER_ID = uuid4()
INVITED_USER_ID = uuid4()


def result_for_scalar(value):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


def result_for_rows(rows):
    result = Mock()
    result.all.return_value = rows
    return result


def result_for_scalar_rows(rows):
    result = Mock()
    result.scalars.return_value.all.return_value = rows
    return result


def user(*, user_id, email, first_name=None, last_name=None):
    return SimpleNamespace(
        id=user_id,
        email=email,
        first_name=first_name,
        last_name=last_name 
    )


class TestGetPropertyMembers:
    @pytest.mark.asyncio
    async def test_requires_claims(self):
        db = Mock()
        db.execute = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await service.get_property_members_handler(PROPERTY_ID, db, None)

        assert exc_info.value.status_code == 401
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_not_found_when_requesting_user_does_not_exist(self):
        db = Mock()
        db.execute = AsyncMock(return_value=result_for_scalar(None))

        with pytest.raises(HTTPException) as exc_info:
            await service.get_property_members_handler(PROPERTY_ID, db, CLAIMS)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_members_with_admin_flags(self):
        current_user = user(
            user_id=INVITER_ID,
            email="admin@example.com",
            first_name="Ava",
            last_name="Admin" 
        )
        member = user(
            user_id=INVITED_USER_ID,
            email="member@example.com",
            first_name="Mia",
            last_name="Member" 
        )
        db = Mock()
        db.execute = AsyncMock(
            side_effect=[
                result_for_scalar(current_user),
                result_for_rows([(current_user, True), (member, False)]),
            ]
        )

        response = await service.get_property_members_handler(
            PROPERTY_ID,
            db,
            CLAIMS 
        )

        assert len(response.members) == 2
        assert response.members[0].user_id == INVITER_ID
        assert response.members[0].email == "admin@example.com"
        assert response.members[0].is_admin is True
        assert response.members[1].user_id == INVITED_USER_ID
        assert response.members[1].is_admin is False
        assert db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_returns_empty_member_list_when_property_has_no_members(self):
        current_user = user(user_id=INVITER_ID, email="admin@example.com")
        db = Mock()
        db.execute = AsyncMock(
            side_effect=[
                result_for_scalar(current_user),
                result_for_rows([]) 
            ]
        )

        response = await service.get_property_members_handler(
            PROPERTY_ID,
            db,
            CLAIMS
        )

        assert response.members == []

    @pytest.mark.asyncio
    async def test_converts_unexpected_database_errors_to_http_500(self):
        db = Mock()
        db.execute = AsyncMock(side_effect=RuntimeError("database unavailable"))

        with pytest.raises(HTTPException) as exc_info:
            await service.get_property_members_handler(PROPERTY_ID, db, CLAIMS)

        assert exc_info.value.status_code == 500
        assert "Failed to fetch members" in exc_info.value.detail
        assert "database unavailable" in exc_info.value.detail


class TestInvitePropertyMember:
    def setup_method(self):
        self.inviter = user(
            user_id=INVITER_ID,
            email="admin@example.com",
            first_name="Ava",
            last_name="Admin" 
        )
        self.property_obj = SimpleNamespace(
            id=PROPERTY_ID,
            address="12 Main Street" 
        )
        self.invited_user = user(
            user_id=INVITED_USER_ID,
            email="member@example.com" 
        )
        self.db = Mock()
        self.db.execute = AsyncMock()
        self.db.add = Mock()
        self.db.commit = AsyncMock()
        self.db.rollback = AsyncMock()
        self.request = InvitePropertyReq(email=self.invited_user.email)

    @pytest.mark.asyncio
    async def test_requires_claims(self):
        with pytest.raises(HTTPException) as exc_info:
            await service.invite_property_member_handler(
                self.request,
                PROPERTY_ID,
                self.db,
                None
            )

        assert exc_info.value.status_code == 401
        self.db.execute.assert_not_awaited()
        self.db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_not_found_when_inviter_does_not_exist(self):
        self.db.execute.return_value = result_for_scalar(None)

        with pytest.raises(HTTPException) as exc_info:
            await service.invite_property_member_handler(
                self.request,
                PROPERTY_ID,
                self.db,
                CLAIMS 
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Inviting user not found"
        self.db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_not_found_when_property_does_not_exist(self):
        self.db.execute.side_effect = [
            result_for_scalar(self.inviter),
            result_for_scalar(None) 
        ]

        with pytest.raises(HTTPException) as exc_info:
            await service.invite_property_member_handler(
                self.request,
                PROPERTY_ID,
                self.db,
                CLAIMS 
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Property not found"
        self.db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_not_found_when_invited_email_is_unknown(self):
        self.db.execute.side_effect = [
            result_for_scalar(self.inviter),
            result_for_scalar(self.property_obj),
            result_for_scalar(None)
        ]

        with pytest.raises(HTTPException) as exc_info:
            await service.invite_property_member_handler(
                self.request,
                PROPERTY_ID,
                self.db,
                CLAIMS
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User with that email does not exist"
        self.db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rejects_existing_property_member(self):
        existing_membership = SimpleNamespace(
            property_id=PROPERTY_ID,
            user_id=INVITED_USER_ID,
            is_admin=False
        )
        self.db.execute.side_effect = [
            result_for_scalar(self.inviter),
            result_for_scalar(self.property_obj),
            result_for_scalar(self.invited_user),
            result_for_scalar(existing_membership)
        ]

        with pytest.raises(HTTPException) as exc_info:
            await service.invite_property_member_handler(
                self.request,
                PROPERTY_ID,
                self.db,
                CLAIMS,


            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "User is already a property member"
        self.db.add.assert_not_called()
        self.db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_adds_member_commits_and_sends_invitation_email(self):
        self.db.execute.side_effect = [
            result_for_scalar(self.inviter),
            result_for_scalar(self.property_obj),
            result_for_scalar(self.invited_user),
            result_for_scalar(None)

        ]

        with patch.object(
            service,
            "send_property_invite_email",
            return_value=(True, None),
        ) as send_email:
            response = await service.invite_property_member_handler(
                self.request,
                PROPERTY_ID,
                self.db,
                CLAIMS
            )

        assert response == {
            "message": "Property member invited successfully",
            "email_sent": True,
        }
        self.db.add.assert_called_once()
        added_membership = self.db.add.call_args.args[0]
        assert added_membership.property_id == PROPERTY_ID
        assert added_membership.user_id == INVITED_USER_ID
        assert added_membership.is_admin is False
        self.db.commit.assert_awaited_once()
        send_email.assert_called_once_with(
            "member@example.com",
            "12 Main Street",
            "Ava Admin"

        )

    @pytest.mark.asyncio
    async def test_keeps_membership_when_invitation_email_fails(self):
        self.db.execute.side_effect = [
            result_for_scalar(self.inviter),
            result_for_scalar(self.property_obj),
            result_for_scalar(self.invited_user),
            result_for_scalar(None)


        ]

        with patch.object(
            service,
            "send_property_invite_email",
            return_value=(False, "SMTP unavailable"),
        ):
            response = await service.invite_property_member_handler(
                self.request,
                PROPERTY_ID,
                self.db,
                CLAIMS
            )

        assert response["email_sent"] is False
        self.db.add.assert_called_once()
        self.db.commit.assert_awaited_once()
        self.db.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rolls_back_and_returns_500_for_unexpected_invite_errors(self):
        self.db.execute.side_effect = [
            result_for_scalar(self.inviter),
            result_for_scalar(self.property_obj),
            result_for_scalar(self.invited_user),
            result_for_scalar(None)
        ]
        self.db.add.side_effect = RuntimeError("insert failed")

        with pytest.raises(HTTPException) as exc_info:
            await service.invite_property_member_handler(
                self.request,
                PROPERTY_ID,
                self.db,
                CLAIMS

            )

        assert exc_info.value.status_code == 500
        assert "Failed to invite property member" in exc_info.value.detail
        self.db.rollback.assert_awaited_once()
        self.db.commit.assert_not_awaited()


class TestRemovePropertyMember:
    def setup_method(self):
        self.db = Mock()
        self.db.execute = AsyncMock()
        self.db.commit = AsyncMock()
        self.db.rollback = AsyncMock()

    @pytest.mark.asyncio
    async def test_requires_claims(self):
        with pytest.raises(HTTPException) as exc_info:
            await service.remove_property_member_handler(
                PROPERTY_ID,
                INVITED_USER_ID,
                self.db,
                None 
            )

        assert exc_info.value.status_code == 401
        self.db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_not_found_when_user_is_not_a_member(self):
        self.db.execute.return_value = result_for_scalar(None)

        with pytest.raises(HTTPException) as exc_info:
            await service.remove_property_member_handler(
                PROPERTY_ID,
                INVITED_USER_ID,
                self.db,
                CLAIMS

            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User is not a member of this property"
        self.db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rejects_removing_the_last_property_admin(self):
        membership = SimpleNamespace(is_admin=True)
        self.db.execute.side_effect = [
            result_for_scalar(membership),
            result_for_scalar_rows([membership])
        ]

        with pytest.raises(HTTPException) as exc_info:
            await service.remove_property_member_handler(
                PROPERTY_ID,
                INVITER_ID,
                self.db,
                CLAIMS 
            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == (
            "The last property administrator cannot be removed"
        )
        self.db.commit.assert_not_awaited()
        assert self.db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_removes_admin_when_another_admin_exists(self):
        membership = SimpleNamespace(is_admin=True)
        another_admin = SimpleNamespace(is_admin=True)
        self.db.execute.side_effect = [
            result_for_scalar(membership),
            result_for_scalar_rows([membership, another_admin]),
            Mock() 
        ]

        response = await service.remove_property_member_handler(
            PROPERTY_ID,
            INVITER_ID,
            self.db,
            CLAIMS
        )

        assert response is None
        assert self.db.execute.await_count == 3
        self.db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_removes_non_admin_member_without_counting_admins(self):
        membership = SimpleNamespace(is_admin=False)
        self.db.execute.side_effect = [
            result_for_scalar(membership),
            Mock()
        ]

        await service.remove_property_member_handler(
            PROPERTY_ID,
            INVITED_USER_ID,
            self.db,
            CLAIMS

            
        )

        assert self.db.execute.await_count == 2
        self.db.commit.assert_awaited_once()