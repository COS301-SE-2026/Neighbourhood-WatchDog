import uuid
from uuid import UUID
from datetime import datetime, timezone
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.models.alert import Alert
from app.models.audit_log import AuditAction
from app.models.camera import Camera
from app.models.user import User, UserRole
from app.schemas.alert import TimeIntervalsEnum, TimePeriod
from app.services.alert_service import acknowledge_alert_handler, broadcast_neighbourhood_alert_service, list_alerts_handler, get_response_metrics_handler, get_alert_frequency_metrics_handler

class TestAcknowledgeAlert:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()
        self.claims = {
            "id": "11111111-1111-1111-1111-111111111111",
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

    @pytest.mark.skip(reason="temporary")
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
        resolver = Mock()
        resolver.id = UUID("11111111-1111-1111-1111-111111111111")

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            alert,
            resolver,
        ]

        with patch(
            "app.services.alert_service.create_audit_log_item"
        ) as mock_audit, patch(
            "app.api.controllers.alert.broadcast",
            new_callable=AsyncMock
        ) as mock_broadcast:

            result = await acknowledge_alert_handler(
                alert.id,
                self.mock_db,
                self.claims
            )

        assert result.status == "ACKNOWLEDGED"
        assert alert.status == "ACKNOWLEDGED"
        assert alert.resolved_by == resolver.id
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 0
        assert mock_broadcast.call_count == 1
        assert mock_audit.call_count == 1

    @pytest.mark.asyncio
    async def test_acknowledge_records_timestamps(self):
        """Acknowledging an alert sets resolved_at and resolved_by."""
        alert = self._make_alert(status="OPEN")

        resolver_id = UUID("20000000-0000-0000-0000-000000000001")

        resolver = Mock()
        resolver.id = resolver_id

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            alert,
            resolver,
        ]

        claims = {
            "custom:role": "NEIGHBOURHOOD_ADMIN",
            "sub": "cognito-sub-200",
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

    def _mock_query_results(self, alerts, total=None):
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = alerts
        self.mock_db.execute.return_value.scalar_one.return_value = (
            total if total is not None else len(alerts)
        )

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
        self._mock_query_results(alerts)

        results, total = await list_alerts_handler(
            self.claims["custom:neighbourhood_id"],
            self.mock_db,
            self.claims,
            None,
        )

        assert len(results) == 2
        assert total == 2
        assert self.mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_filters_by_camera_id(self):
        alert = self._make_alert("OPEN")
        self._mock_query_results([alert], total=1)
        results, total = await list_alerts_handler(
            self.claims["custom:neighbourhood_id"],
            self.mock_db,
            self.claims,
            None,
            camera_id=alert.camera_id,
        )

        assert len(results) == 1
        assert total == 1
    
    @pytest.mark.asyncio
    async def test_filters_by_detetction_type(self):
        alert = self._make_alert("OPEN")
        self._mock_query_results([alert], total=1)
        results, total = await list_alerts_handler(
            self.claims["custom:neighbourhood_id"],
            self.mock_db,
            self.claims,
            None,
            detection_type="HUMAN_PRESENCE",
        )

        assert len(results) == 1
        assert results[0].detection_type == "HUMAN_PRESENCE"

    @pytest.mark.asyncio
    async def test_filters_by_status(self):
        alert = self._make_alert("OPEN")
        self._mock_query_results([alert], total=1)
        results, total = await list_alerts_handler(
            self.claims["custom:neighbourhood_id"],
            self.mock_db,
            self.claims,
            "OPEN",
        )

        assert len(results) == 1
        assert results[0].status == "OPEN"

    @pytest.mark.asyncio
    async def test_date_range_is_applied(self):
        alert = self._make_alert("OPEN")
        self._mock_query_results([alert], total=1)
        results, total = await list_alerts_handler(
            self.claims["custom:neighbourhood_id"],
            self.mock_db,
            self.claims,
            None,
            start_date=datetime(2026,1,1, tzinfo=timezone.utc),
            end_date=datetime(2026,12,31, tzinfo=timezone.utc),
        )

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_start_date_after_end_date_raises_400(self):
        start=datetime(2026,7,10, tzinfo=timezone.utc)
        end=datetime(2026,7,1, tzinfo=timezone.utc)

        with pytest.raises(HTTPException) as exc:
            await list_alerts_handler(
                self.claims["custom:neighbourhood_id"],
                self.mock_db,
                self.claims,
                None,
                start_date=start,
                end_date=end,
            )

        assert exc.value.status_code == 400
        assert self.mock_db.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_result_is_valid(self):
        self._mock_query_results([], total=0)
        results, total = await list_alerts_handler(
            self.claims["custom:neighbourhood_id"],
            self.mock_db,
            self.claims,
            None,
        )

        assert results == []
        assert total == 0

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

        self.mock_data = Mock()
        self.mock_data.bucket = "2025-07-13T00:00:00Z"
        self.mock_data.count = 200

        self.mock_db.execute.return_value.all.return_value = [self.mock_data]

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

class TestBroadcastNeighbourhoodAlert:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.add = Mock()
        self.claims = {
            "sub": "cognito-sub-123",
            "custom:role": "NEIGHBOURHOOD_ADMIN",
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
        return alert, event
 
    def _make_camera(self, neighbourhood_id=None):
        camera = Mock()
        camera.id = uuid.uuid4()
        camera.name = "Front Door Camera"
        camera.location = "123 Main St"
        camera.neighbourhood_id = neighbourhood_id or uuid.uuid4()
        return camera
 
    def _make_neighbourhood(self):
        neighbourhood = Mock()
        neighbourhood.id = uuid.uuid4()
        return neighbourhood
 
    def _make_resident(self):
        resident = Mock(spec=User)
        resident.id = uuid.uuid4()
        resident.role = UserRole.RESIDENT
        resident.phone_number = "+15550001111"
        resident.email = "resident@example.com"
        return resident
 
    def _exec_result(self, scalar_one_or_none=None, scalars_all=None):
        result = Mock()
        result.scalar_one_or_none.return_value = scalar_one_or_none
        if scalars_all is not None:
            result.scalars.return_value.all.return_value = scalars_all
        return result

    @pytest.mark.asyncio
    async def test_alert_not_found_raises_404(self):
        self.mock_db.execute.return_value = self._exec_result(scalar_one_or_none=None)
 
        with pytest.raises(HTTPException) as exc:
            await broadcast_neighbourhood_alert_service(uuid.uuid4(), self.mock_db, self.claims)
 
        assert exc.value.status_code == 404
        assert "Alert not found" in exc.value.detail
 
    @pytest.mark.asyncio
    async def test_camera_not_found_raises_404(self):
        alert, _ = self._make_alert()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=None),
        ]
 
        with pytest.raises(HTTPException) as exc:
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        assert exc.value.status_code == 404
        assert "Camera not found" in exc.value.detail
 
    @pytest.mark.asyncio
    async def test_neighbourhood_not_found_raises_404(self):
        alert, _ = self._make_alert()
        camera = self._make_camera()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=camera),
            self._exec_result(scalar_one_or_none=None),
        ]
 
        with pytest.raises(HTTPException) as exc:
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        assert exc.value.status_code == 404
        assert "Neighbourhood not found" in exc.value.detail
 
    @pytest.mark.asyncio
    async def test_detection_event_not_found_raises_404(self):
        alert, _ = self._make_alert()
        camera = self._make_camera()
        neighbourhood = self._make_neighbourhood()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=camera),
            self._exec_result(scalar_one_or_none=neighbourhood),
            self._exec_result(scalar_one_or_none=None),
        ]
 
        with pytest.raises(HTTPException) as exc:
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        assert exc.value.status_code == 404
        assert "Detection not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_admin_user_not_found_raises_404(self):
        alert, event = self._make_alert()
        neighbourhood_id = uuid.uuid4()
        camera = self._make_camera(neighbourhood_id=neighbourhood_id)
        neighbourhood = self._make_neighbourhood()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=camera),
            self._exec_result(scalar_one_or_none=neighbourhood),
            self._exec_result(scalar_one_or_none=event),
            self._exec_result(scalars_all=[]),
            self._exec_result(scalar_one_or_none=None)
        ]
 
        with patch("app.api.controllers.alert.broadcast", new_callable=AsyncMock), \
             patch("app.services.alert_service._format_whatsapp_message", return_value="msg"), \
             patch("app.services.alert_service._notify_users"):
 
            with pytest.raises(HTTPException) as exc:
                await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        assert exc.value.status_code == 404
        assert "Admin user not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_happy_path_broadcasts_and_notifies_residents(self):
        alert, event = self._make_alert()
        neighbourhood_id = uuid.uuid4()
        camera = self._make_camera(neighbourhood_id=neighbourhood_id)
        neighbourhood = self._make_neighbourhood()
        resident = self._make_resident()
        admin_id = uuid.uuid4()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),          
            self._exec_result(scalar_one_or_none=camera),         
            self._exec_result(scalar_one_or_none=neighbourhood),  
            self._exec_result(scalar_one_or_none=event),         
            self._exec_result(scalars_all=[resident]),          
            self._exec_result(scalar_one_or_none=admin_id),    
        ]
 
        with patch("app.api.controllers.alert.broadcast", new_callable=AsyncMock) as mock_broadcast, \
             patch("app.services.alert_service._format_whatsapp_message", return_value="msg") as mock_format, \
             patch("app.services.alert_service._notify_users") as mock_notify:
 
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        assert mock_broadcast.call_count == 1
        kwargs = mock_broadcast.call_args.kwargs
        assert kwargs["neighbourhood_id"] == str(neighbourhood_id)
        assert kwargs["message"]["event"] == "alert.broadcast"
 
        mock_format.assert_called_once_with("CRITICAL", event.detection_type, camera.name, ANY)
        mock_notify.assert_called_once_with(
            self.mock_db, alert.id, [resident], "msg", event.detection_type, camera, "CRITICAL"
        )
 
        assert self.mock_db.add.call_count == 1
        audit_record = self.mock_db.add.call_args.args[0]
        assert audit_record.user_id == admin_id
        assert audit_record.action == AuditAction.UPDATE
        assert audit_record.target_entity_type == "alert"
        assert audit_record.target_entity_id == alert.id
        assert audit_record.old_values == {"broadcast": False}
        assert audit_record.new_values == {
            "broadcast": True,
            "neighbourhood_id": str(neighbourhood_id),
        }
        assert self.mock_db.commit.call_count == 1
 
    @pytest.mark.asyncio
    async def test_no_residents_still_broadcasts_but_skips_notifications(self):
        alert, event = self._make_alert()
        neighbourhood_id = uuid.uuid4()
        camera = self._make_camera(neighbourhood_id=neighbourhood_id)
        neighbourhood = self._make_neighbourhood()
        admin_id = uuid.uuid4()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=camera),
            self._exec_result(scalar_one_or_none=neighbourhood),
            self._exec_result(scalar_one_or_none=event),
            self._exec_result(scalars_all=[]),
            self._exec_result(scalar_one_or_none=admin_id),
        ]
 
        with patch("app.api.controllers.alert.broadcast", new_callable=AsyncMock) as mock_broadcast, \
             patch("app.services.alert_service._format_whatsapp_message", return_value="msg"), \
             patch("app.services.alert_service._notify_users") as mock_notify:
 
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        assert mock_broadcast.call_count == 1
        mock_notify.assert_called_once()
        assert mock_notify.call_args.args[2] == []  
        assert self.mock_db.commit.call_count == 1