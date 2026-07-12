import uuid
from uuid import UUID
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.models.alert import Alert
from app.models.camera import Camera
from app.schemas.alert import TimeIntervalsEnum, TimePeriod
from app.services.alert_service import acknowledge_alert_handler, list_alerts_handler, get_response_metrics_handler, get_alert_frequency_metrics_handler

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

    @pytest.mark.asyncio
    async def test_acknowledge_records_timestamps(self):
        """Acknowledging an alert sets resolved_at and resolved_by."""
        alert = self._make_alert(status="OPEN")

        self.mock_db.execute.return_value.scalar_one_or_none.return_value = [alert]

        claims = {
            "custom:role": "NEIGHBOURHOOD_ADMIN",
            "sub": "20000000-0000-0000-0000-000000000001",
            "custom:neighbourhood_id": str(uuid.uuid4()),
        }

        with patch(
            "app.api.controllers.alert.broadcast",
            new_callable=AsyncMock,
        ):
            await acknowledge_alert_handler(
                alert.id,
                self.mock_db,
                claims,
            )

        assert alert.status == "ACKNOWLEDGED"
        assert alert.resolved_at is not None
        assert alert.resolved_by == UUID(
            "20000000-0000-0000-0000-000000000001"
        )



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


class TestResponseMetrics:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.claims = {
            "custom:neighbourhood_id": "10000000-0000-0000-0000-000000000001",
        }

    def test_metrics_returns_pending_for_open_alerts(self):
        """OPEN alerts show as PENDING in metrics."""
        alert = Mock()
        alert.id = UUID("aaaaaaaa-0000-0000-0000-000000000001")
        alert.camera_id = UUID("40000000-0000-0000-0000-000000000001")
        alert.status = "OPEN"
        alert.resolved_at = None
        alert.resolved_by = None
        alert.created_at = datetime(
            2026,
            7,
            5,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )

        self.mock_db.execute.return_value.scalars.return_value.all.return_value = [
            alert
        ]

        result = get_response_metrics_handler(
            UUID("10000000-0000-0000-0000-000000000001"),
            self.mock_db,
            self.claims,
        )

        assert result.pending_count == 1
        assert result.acknowledged_count == 0
        assert result.average_response_seconds is None
        assert result.items[0].status == "PENDING"
        assert result.items[0].response_seconds is None

class TestFrequencyMetrics:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.claims = {
            "custom:neighbourhood_id": "10000000-0000-0000-0000-000000000001",
        }

        self.mock_db.execute.return_value.all.return_value = []

    @pytest.mark.asyncio
    async def test_happy_case(self):
        result = await get_alert_frequency_metrics_handler(
            neighbourhood_id=UUID("10000000-0000-0000-0000-000000000001"),
            db=self.mock_db,
            time_interval=TimeIntervalsEnum.DAILY,
            time_period=TimePeriod.MONTH,
            claims=self.claims
        )

        assert result.status == 200
        assert len(result.data) == 0

    @pytest.mark.asyncio
    async def test_incorrect_claims(self):
        self.claims = {
            "custom:neighbourhood_id": "10000000-0000-0000-0000-000000000002",
        }

        with pytest.raises(HTTPException) as exception:
            _ = await get_alert_frequency_metrics_handler(
                neighbourhood_id=UUID("10000000-0000-0000-0000-000000000001"),
                db=self.mock_db,
                time_interval=TimeIntervalsEnum.DAILY,
                time_period=TimePeriod.MONTH,
                claims=self.claims
            )
        
        assert exception.value.status_code == 403
        assert self.mock_db.select.call_count == 0
        assert self.mock_db.join.call_count == 0

    @pytest.mark.asyncio
    async def test_no_db(self):
        with pytest.raises(HTTPException) as exception:
            _ = await get_alert_frequency_metrics_handler(
                neighbourhood_id=UUID("10000000-0000-0000-0000-000000000001"),
                db=None,
                time_interval=TimeIntervalsEnum.DAILY,
                time_period=TimePeriod.MONTH,
                claims=self.claims
            )
        
        assert exception.value.status_code == 500
        assert self.mock_db.select.call_count == 0
        assert self.mock_db.join.call_count == 0
    
    @pytest.mark.asyncio
    async def test_no_time_interval(self):
        with pytest.raises(HTTPException) as exception:
            _ = await get_alert_frequency_metrics_handler(
                neighbourhood_id=UUID("10000000-0000-0000-0000-000000000001"),
                db=self.mock_db,
                time_interval=None,
                time_period=TimePeriod.MONTH,
                claims=self.claims
            )
        
        assert exception.value.status_code == 400
        assert self.mock_db.select.call_count == 0
        assert self.mock_db.join.call_count == 0

    @pytest.mark.asyncio
    async def test_no_claims(self):
        with pytest.raises(HTTPException) as exception:
            _ = await get_alert_frequency_metrics_handler(
                neighbourhood_id=UUID("10000000-0000-0000-0000-000000000001"),
                db=self.mock_db,
                time_interval=TimeIntervalsEnum.DAILY,
                time_period=TimePeriod.MONTH,
                claims=None
            )
        
        assert exception.value.status_code == 401
        assert self.mock_db.select.call_count == 0
        assert self.mock_db.join.call_count == 0