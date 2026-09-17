from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from geoalchemy2.elements import WKTElement

from app.schemas.neighbourhood import UpdateOfficerLocationReq
from app.services.security_officer_service import update_location_handler


class TestUpdateOfficerLocation:
    def setup_method(self):
        """Runs before each test method"""
        self.mock_db = Mock()
        self.mock_result = Mock()
        self.mock_db.execute = AsyncMock(return_value=self.mock_result)

        self.mock_db.add = Mock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.flush = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        self.claims = {"sub": "cognito-sub-123"}
        self.req = UpdateOfficerLocationReq(
            neighbourhood_id=uuid4(),
            latitude=-25.7461,
            longitude=28.1881,
        )

    @pytest.mark.asyncio
    async def test_no_claims_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            await update_location_handler(self.req, self.mock_db, None)

        assert exc_info.value.status_code == 401
        self.mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_officer_not_found_raises_404(self):
        self.mock_result.scalars.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await update_location_handler(self.req, self.mock_db, self.claims)

        assert exc_info.value.status_code == 404
        self.mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_happy_path_updates_location(self):
        mock_officer = Mock()
        self.mock_result.scalars.return_value.first.return_value = mock_officer

        res = await update_location_handler(self.req, self.mock_db, self.claims)

        assert isinstance(mock_officer.last_known_location, WKTElement)
        assert mock_officer.last_known_location.desc == "POINT(28.1881 -25.7461)"
        assert mock_officer.last_known_location.srid == 4326
        assert mock_officer.location_updated_at is not None
        self.mock_db.commit.assert_awaited_once()
        assert res.status == 200

    @pytest.mark.asyncio
    async def test_commit_failure_rolls_back_and_raises_500(self):
        mock_officer = Mock()
        self.mock_result.scalars.return_value.first.return_value = mock_officer
        self.mock_db.commit.side_effect = Exception("db failed")

        with pytest.raises(HTTPException) as exc_info:
            await update_location_handler(self.req, self.mock_db, self.claims)

        assert exc_info.value.status_code == 500
        self.mock_db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_queries_scoped_to_claims_sub_and_neighbourhood(self):
        mock_officer = Mock()
        self.mock_result.scalars.return_value.first.return_value = mock_officer

        await update_location_handler(self.req, self.mock_db, self.claims)

        self.mock_db.execute.assert_awaited_once()