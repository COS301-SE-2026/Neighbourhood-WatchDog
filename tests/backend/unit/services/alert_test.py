import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.models.alert import Alert
from app.models.camera import Camera
from app.services.alert_service import acknowledge_alert_handler, list_alerts_handler


class TestAcknowledgeAlert:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()
        self.claims = {
            "sub": "cognito-sub-123",
            "custom:role": "SECURITY_OFFICER",
            "custom:neighbourhood_id": str(uuid.uuid4()),
        }

        self.alert_patcher = patch("app.services.alert_service.Alert", new=Alert)
        self.camera_patcher = patch("app.services.alert_service.Camera", new=Camera)

        self.alert_patcher.start()
        self.camera_patcher.start()

    def teardown_method(self):
        self.alert_patcher.stop()
        self.camera_patcher.stop()

    def _make_alert(self, status: str = "OPEN"):
        event = Mock()
        event.detection_type = "HUMAN_PRESENCE"
        event.confidence_score = 0.8
        event.thumbnail_url = None

        alert = Mock()
        alert.id = uuid.uuid4()
        alert.camera_id = uuid.uuid4()
        alert.detection_event_id = uuid.uuid4()
        alert.status = status
        alert.resolved_by = None
        alert.resolved_at = None
        alert.created_at = datetime.now(timezone.utc)
        alert.detection_event = event
        return alert

    @pytest.mark.asyncio
    async def test_missing_alert_id_raises_400(self):
        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(None, self.mock_db, self.claims)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_db_raises_500(self):
        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(uuid.uuid4(), None, self.claims)

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_missing_claims_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(uuid.uuid4(), self.mock_db, None)

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_role_raises_403(self):
        claims = {"sub": "cognito-sub-123", "custom:role": "RESIDENT"}
        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(uuid.uuid4(), self.mock_db, claims)

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_alert_not_found_raises_404(self):
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [None]

        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(uuid.uuid4(), self.mock_db, self.claims)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_already_acknowledged_raises_409(self):
        alert = self._make_alert(status="ACKNOWLEDGED")
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [alert]

        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(alert.id, self.mock_db, self.claims)

        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_happy_path_acknowledges_alert(self):
        alert = self._make_alert(status="OPEN")
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [alert]

        with patch("app.api.controllers.alert.broadcast", new_callable=AsyncMock) as mock_broadcast:
            result = await acknowledge_alert_handler(alert.id, self.mock_db, self.claims)

        assert result.status == "ACKNOWLEDGED"
        assert alert.status == "ACKNOWLEDGED"
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert mock_broadcast.call_count == 1


class TestListAlerts:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.mock_db.rollback = Mock()
        self.claims = {
            "sub": "cognito-sub-123",
            "custom:role": "RESIDENT",
            "custom:neighbourhood_id": str(uuid.uuid4()),
        }

        self.alert_patcher = patch("app.services.alert_service.Alert", new=Alert)
        self.camera_patcher = patch("app.services.alert_service.Camera", new=Camera)

        self.alert_patcher.start()
        self.camera_patcher.start()

    def teardown_method(self):
        self.alert_patcher.stop()
        self.camera_patcher.stop()

    def _make_alert(self, status: str):
        event = Mock()
        event.detection_type = "HUMAN_PRESENCE"
        event.confidence_score = 0.8
        event.thumbnail_url = None

        alert = Mock()
        alert.id = uuid.uuid4()
        alert.camera_id = uuid.uuid4()
        alert.detection_event_id = uuid.uuid4()
        alert.status = status
        alert.resolved_by = None
        alert.resolved_at = None
        alert.created_at = datetime.now(timezone.utc)
        alert.detection_event = event
        return alert

    @pytest.mark.asyncio
    async def test_missing_neighbourhood_id_raises_400(self):
        with pytest.raises(HTTPException) as exc:
            await list_alerts_handler(None, self.mock_db, self.claims, None)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_db_raises_500(self):
        with pytest.raises(HTTPException) as exc:
            await list_alerts_handler(str(uuid.uuid4()), None, self.claims, None)

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_missing_claims_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            await list_alerts_handler(str(uuid.uuid4()), self.mock_db, None, None)

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_neighbourhood_raises_403(self):
        claims = {
            "sub": "cognito-sub-123",
            "custom:role": "RESIDENT",
            "custom:neighbourhood_id": str(uuid.uuid4()),
        }

        with pytest.raises(HTTPException) as exc:
            await list_alerts_handler(str(uuid.uuid4()), self.mock_db, claims, None)

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_list_alerts_happy_path(self):
        alerts = [self._make_alert("OPEN"), self._make_alert("ACKNOWLEDGED")]
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = alerts

        results = await list_alerts_handler(
            self.claims["custom:neighbourhood_id"],
            self.mock_db,
            self.claims,
            None,
        )

        assert len(results) == 2
        assert self.mock_db.execute.call_count == 1
