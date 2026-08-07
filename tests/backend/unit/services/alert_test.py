import uuid
from uuid import UUID
from datetime import datetime, timezone
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.models.alert import Alert
from app.models.audit_log import AuditAction, TargetEntity
from app.models.camera import Camera
from app.models.user import User, UserRole
from app.schemas.alert import TimeIntervalsEnum, TimePeriod
from app.services.alert_service import acknowledge_alert_handler, broadcast_neighbourhood_alert_service, list_alerts_handler, get_response_metrics_handler, get_alert_frequency_metrics_handler

class TestAcknowledgeAlert:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        
        self.user_id = UUID("11111111-1111-1111-1111-111111111111")
        self.neighbourhood_id = uuid.uuid4()

        self.claims = {
            "id": str(self.user_id),
            "sub": "cognito-sub-123",
        }

        self.alert_patcher = patch("app.services.alert_service.Alert", new=Alert)
        self.camera_patcher = patch("app.services.alert_service.Camera", new=Camera)

        self.alert_patcher.start()
        self.camera_patcher.start()

    def teardown_method(self):
        self.alert_patcher.stop()
        self.camera_patcher.stop()

    def _make_alert(self, status: str = "OPEN"):
        alert = Mock()
        alert.id = uuid.uuid4()
        alert.camera_id = uuid.uuid4()
        alert.frame_timestamp = datetime.now(timezone.utc)
        alert.detection_type = "HUMAN_PRESENCE"
        alert.confidence_score = 0.8
        alert.thumbnail_url = None
        alert.clip_s3_key = None
        alert.clip_expires_at = None
        alert.processed = True
        alert.status = status
        alert.resolved_by = None
        alert.resolved_at = None
        alert.created_at = datetime.now(timezone.utc)
        return alert

    def _exec_result(self, scalar_one_or_none=None):
        result = Mock()
        result.scalar_one_or_none.return_value = scalar_one_or_none
        return result

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
        self.mock_db.execute.return_value = self._exec_result(
            scalar_one_or_none=None
        )

        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(uuid.uuid4(), self.mock_db, self.claims)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_already_acknowledged_raises_409(self):
        alert = self._make_alert(status="ACKNOWLEDGED")
        self.mock_db.execute.return_value = self._exec_result(
            scalar_one_or_none=alert
        )

        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(alert.id, self.mock_db, self.claims)

        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_happy_path_acknowledges_alert(self):
        alert = self._make_alert(status="OPEN")
        neighbourhood_result = self._exec_result(
            scalar_one_or_none=self.neighbourhood_id,
            )

        membership = Mock()
        membership.user_id = self.user_id
        membership.neighbourhood_id = self.neighbourhood_id

        membership_result = self._exec_result(
            scalar_one_or_none=membership,
        )

        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            neighbourhood_result,
            membership_result,
        ]

        with (patch(
            "app.services.alert_service.create_audit_log_item",
            new_callable=AsyncMock,
        ) as mock_audit,
        patch(
            "app.services.alert_service._get_neighbourhood_websocket_recipient_ids",
            new_callable=AsyncMock,
            return_value=[str(self.user_id)],
        ),
        patch(
            "app.api.controllers.alert.broadcast",
            new_callable=AsyncMock
        ) as mock_broadcast):

            result = await acknowledge_alert_handler(
                alert.id,
                self.mock_db,
                self.claims
            )

        assert result.status == "ACKNOWLEDGED"
        assert alert.status == "ACKNOWLEDGED"
        assert alert.resolved_by == self.user_id

        self.mock_db.commit.assert_awaited_once()
        mock_audit.assert_awaited_once()
        mock_broadcast.assert_awaited_once()
        assert self.mock_db.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_acknowledge_records_timestamps(self):
        """Acknowledging an alert sets resolved_at and resolved_by."""
        alert = self._make_alert(status="OPEN")
        neighbourhood_id = uuid.uuid4()

        membership = Mock()
        membership.user_id = self.user_id
        membership.neighbourhood_id = neighbourhood_id

        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=neighbourhood_id),
            self._exec_result(scalar_one_or_none=membership),
        ]

        with (
            patch(
                "app.services.alert_service._get_neighbourhood_websocket_recipient_ids",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "app.api.controllers.alert.broadcast",
                new_callable=AsyncMock,
            ),
        ):
            await acknowledge_alert_handler(
                alert.id,
                self.mock_db,
                self.claims,
            )

        assert alert.status == "ACKNOWLEDGED"
        assert alert.resolved_at is not None
        assert alert.resolved_by == self.user_id



class TestListAlerts:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        self.user_id = uuid.uuid4()
        self.neighbourhood_id = uuid.uuid4()

        self.claims = {
            "id": str(self.user_id),
            "sub": "cognito-sub-123",
        }

        self.alert_patcher = patch("app.services.alert_service.Alert", new=Alert)
        self.camera_patcher = patch("app.services.alert_service.Camera", new=Camera)

        self.alert_patcher.start()
        self.camera_patcher.start()

    def teardown_method(self):
        self.alert_patcher.stop()
        self.camera_patcher.stop()

    def _make_alert(self, status: str):
        alert = Mock()
        alert.id = uuid.uuid4()
        alert.camera_id = uuid.uuid4()
        alert.frame_timestamp = datetime.now(timezone.utc)
        alert.detection_type = "HUMAN_PRESENCE"
        alert.confidence_score = 0.8
        alert.thumbnail_url = None
        alert.clip_s3_key = None
        alert.clip_expires_at = None
        alert.processed = True
        alert.status = status
        alert.resolved_by = None
        alert.resolved_at = None
        alert.created_at = datetime.now(timezone.utc)
        return alert

    def _mock_query_results(self, alerts, total=None):
        membership = Mock()
        membership.user_id = self.user_id
        membership.neighbourhood_id = self.neighbourhood_id

        membership_result = Mock()
        membership_result.scalar_one_or_none.return_value = membership

        count_result = Mock()
        count_result.scalar_one.return_value = (
            total if total is not None else len(alerts)
        )

        alerts_result = Mock()
        alerts_result.scalars.return_value.all.return_value = alerts

        self.mock_db.execute.side_effect = [
            membership_result,
            count_result,
            alerts_result,
        ]

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
    async def test_non_member_raises_403(self):
        membership_result = Mock()
        membership_result.scalar_one_or_none.return_value = None

        self.mock_db.execute.return_value = membership_result

        with pytest.raises(HTTPException) as exc:
            await list_alerts_handler(self.neighbourhood_id, self.mock_db, self.claims, None)

        assert exc.value.status_code == 403
        assert self.mock_db.execute.await_count == 1


    @pytest.mark.asyncio
    async def test_list_alerts_happy_path(self):
        alerts = [self._make_alert("OPEN"), self._make_alert("ACKNOWLEDGED")]
        self._mock_query_results(alerts)

        results, total = await list_alerts_handler(
            self.neighbourhood_id,
            self.mock_db,
            self.claims,
            None,
        )

        assert len(results) == 2
        assert total == 2
        assert self.mock_db.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_filters_by_camera_id(self):
        alert = self._make_alert("OPEN")
        self._mock_query_results([alert], total=1)
        results, total = await list_alerts_handler(
            self.neighbourhood_id,
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
            self.neighbourhood_id,
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
            self.neighbourhood_id,
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
            self.neighbourhood_id,
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
                self.neighbourhood_id,
                self.mock_db,
                self.claims,
                None,
                start_date=start,
                end_date=end,
            )

        assert exc.value.status_code == 400
        assert self.mock_db.execute.await_count == 0

    @pytest.mark.asyncio
    async def test_empty_result_is_valid(self):
        self._mock_query_results([], total=0)
        results, total = await list_alerts_handler(
            self.neighbourhood_id,
            self.mock_db,
            self.claims,
            None,
        )

        assert results == []
        assert total == 0

class TestResponseMetrics:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = AsyncMock()

        self.user_id = UUID("20000000-0000-0000-0000-000000000001")
        self.neighbourhood_id = UUID(
            "10000000-0000-0000-0000-000000000001"
        )

        self.claims = {
            "id": str(self.user_id),
            "sub": "cognito-sub-123",
        }

    @pytest.mark.asyncio
    async def test_metrics_returns_pending_for_open_alerts(self):
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

        membership = Mock()
        membership.user_id = self.user_id
        membership.neighbourhood_id = self.neighbourhood_id

        membership_result = Mock()
        membership_result.scalar_one_or_none.return_value = membership

        alerts_result = Mock()
        alerts_result.scalars.return_value.all.return_value = [alert]

        self.mock_db.execute.side_effect = [
            membership_result,
            alerts_result,
        ]

        result = await get_response_metrics_handler(
            self.neighbourhood_id,
            self.mock_db,
            self.claims,
        )

        assert result.pending_count == 1
        assert result.acknowledged_count == 0
        assert result.average_response_seconds is None
        assert result.items[0].status == "PENDING"
        assert result.items[0].response_seconds is None
        assert self.mock_db.execute.await_count == 2

class TestFrequencyMetrics:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = AsyncMock()
        self.user_id = UUID("20000000-0000-0000-0000-000000000001")
        self.neighbourhood_id = UUID(
            "10000000-0000-0000-0000-000000000001"
        )

        self.claims = {
            "id": str(self.user_id),
            "sub": "cognito-sub-123",
        }

        self.mock_data = Mock()
        self.mock_data.bucket = datetime(
            2026,
            7,
            13,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.mock_data.count = 200

    def _membership_result(self, exists=True):
        result = Mock()
        result.scalar_one_or_none.return_value = Mock() if exists else None
        return result
    
    @pytest.mark.asyncio
    async def test_happy_case(self):
        rows_result = Mock()
        rows_result.all.return_value = [self.mock_data]

        self.mock_db.execute.side_effect = [
            self._membership_result(),
            rows_result,
        ]

        result = await get_alert_frequency_metrics_handler(
            neighbourhood_id=self.neighbourhood_id,
            db=self.mock_db,
            time_interval=TimeIntervalsEnum.DAILY,
            time_period=TimePeriod.MONTH,
            claims=self.claims
        )

        assert result.status == 200
        assert result.data.period == [self.mock_data.bucket]
        assert result.data.count == [self.mock_data.count]
        assert self.mock_db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_incorrect_claims(self):
        self.mock_db.execute.return_value = self._membership_result(
            exists=False,
        )

        with pytest.raises(HTTPException) as exception:
            await get_alert_frequency_metrics_handler(
                neighbourhood_id=self.neighbourhood_id,
                db=self.mock_db,
                time_interval=TimeIntervalsEnum.DAILY,
                time_period=TimePeriod.MONTH,
                claims=self.claims
            )
        
        assert exception.value.status_code == 403
        assert self.mock_db.execute.await_count == 1

    @pytest.mark.asyncio
    async def test_no_db(self):
        with pytest.raises(HTTPException) as exception:
            await get_alert_frequency_metrics_handler(
                neighbourhood_id=self.neighbourhood_id,
                db=None,
                time_interval=TimeIntervalsEnum.DAILY,
                time_period=TimePeriod.MONTH,
                claims=self.claims
            )
        
        assert exception.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_no_time_interval(self):
        with pytest.raises(HTTPException) as exception:
            await get_alert_frequency_metrics_handler(
                neighbourhood_id=self.neighbourhood_id,
                db=self.mock_db,
                time_interval=None,
                time_period=TimePeriod.MONTH,
                claims=self.claims
            )
        
        assert exception.value.status_code == 400
        assert self.mock_db.execute.await_count == 0

    @pytest.mark.asyncio
    async def test_no_claims(self):
        with pytest.raises(HTTPException) as exception:
            _ = await get_alert_frequency_metrics_handler(
                neighbourhood_id=self.neighbourhood_id,
                db=self.mock_db,
                time_interval=TimeIntervalsEnum.DAILY,
                time_period=TimePeriod.MONTH,
                claims=None
            )
        
        assert exception.value.status_code == 401
        assert self.mock_db.execute.await_count == 0

class TestBroadcastNeighbourhoodAlert:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.add = Mock()

        self.user_id = uuid.uuid4()
        self.neighbourhood_id = uuid.uuid4()

        self.claims = {
            "id": str(self.user_id),
            "sub": "cognito-sub-123",
        }

 
        self.alert_patcher = patch("app.services.alert_service.Alert", new=Alert)
        self.camera_patcher = patch("app.services.alert_service.Camera", new=Camera)

        self.alert_patcher.start()
        self.camera_patcher.start()
 
    def teardown_method(self):
        self.alert_patcher.stop()
        self.camera_patcher.stop()
 
    def _make_alert(self, status: str = "OPEN"):
        alert = Mock()
        alert.id = uuid.uuid4()
        alert.camera_id = uuid.uuid4()
        alert.frame_timestamp = datetime.now(timezone.utc)
        alert.detection_type = "HUMAN_PRESENCE"
        alert.confidence_score = 0.8
        alert.thumbnail_url = None
        alert.clip_s3_key = None
        alert.clip_expires_at = None
        alert.processed = True
        alert.status = status
        alert.resolved_by = None
        alert.resolved_at = None
        alert.created_at = datetime.now(timezone.utc)
        return alert
 
    def _make_camera(self, neighbourhood_id=None):
        camera = Mock()
        camera.id = uuid.uuid4()
        camera.name = "Front Door Camera"
        camera.location = "123 Main St"
        camera.neighbourhood_id = neighbourhood_id or uuid.uuid4()

        property_obj = Mock()
        property_obj.id = camera.property_id
        property_obj.neighbourhood_id = (
            neighbourhood_id or self.neighbourhood_id
        )

        camera.property = property_obj
        return camera
 
    def _make_neighbourhood(self, neighbourhood_id=None):
        neighbourhood = Mock()
        neighbourhood.id = neighbourhood_id or self.neighbourhood_id
        return neighbourhood
 
    def _make_resident(self):
        resident = Mock(spec=User)
        resident.id = uuid.uuid4()
        resident.phone_number = "+15550001111"
        resident.email = "resident@example.com"
        return resident

    def _admin_membership_result(self, exists=True):
        result = Mock()

        if exists:
            membership = Mock()
            membership.user_id = self.user_id
            membership.neighbourhood_id = self.neighbourhood_id
            membership.role = "NEIGHBOURHOOD_ADMIN"
            result.scalar_one_or_none.return_value = membership
        else:
            result.scalar_one_or_none.return_value = None

        return result
 
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
        alert= self._make_alert()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=None),
        ]
 
        with pytest.raises(HTTPException) as exc:
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        assert exc.value.status_code == 404
        assert "Camera not found" in exc.value.detail


    @pytest.mark.asyncio
    async def test_non_admin_member_raises_403(self):
        alert = self._make_alert()
        camera = self._make_camera()

        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=camera),
            self._admin_membership_result(exists=False),
        ]

        with pytest.raises(HTTPException) as exc:
            await broadcast_neighbourhood_alert_service(
                alert.id,
                self.mock_db,
                self.claims,
            )

        assert exc.value.status_code == 403
 
    @pytest.mark.asyncio
    async def test_neighbourhood_not_found_raises_404(self):
        alert = self._make_alert()
        camera = self._make_camera()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=camera),
            self._admin_membership_result(),
            self._exec_result(scalar_one_or_none=None),
        ]
 
        with pytest.raises(HTTPException) as exc:
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        assert exc.value.status_code == 404
        assert "Neighbourhood not found" in exc.value.detail
 
    @pytest.mark.asyncio
    async def test_happy_path_broadcasts_and_notifies_residents(self):
        alert = self._make_alert()
        camera = self._make_camera()
        neighbourhood = self._make_neighbourhood()
        resident = self._make_resident()
 
        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=camera),
            self._admin_membership_result(),
            self._exec_result(scalar_one_or_none=neighbourhood),
            self._exec_result(scalars_all=[resident]),
        ]
 
        with (
            patch(
                "app.services.alert_service._get_neighbourhood_websocket_recipient_ids", 
                new_callable=AsyncMock,
                return_value=[str(resident.id)], 
            ),
            patch("app.api.controllers.alert.broadcast", new_callable=AsyncMock) as mock_broadcast,
            patch("app.services.alert_service._format_whatsapp_message", return_value="msg") as mock_format,
            patch("app.services.alert_service._notify_users") as mock_notify
            ):
 
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        mock_broadcast.assert_awaited_once()
        recipient_ids, message = mock_broadcast.call_args.args

        assert recipient_ids == [str(resident.id)]
        assert message["event"] == "alert.broadcast"
 
        mock_format.assert_called_once_with("CRITICAL", alert.detection_type, camera.name, ANY)
        mock_notify.assert_called_once_with(
            self.mock_db, alert.id, [resident], "msg", alert.detection_type, camera, "CRITICAL"
        )
 
        self.mock_db.add.assert_called_once()

        audit_record = self.mock_db.add.call_args.args[0]
        assert audit_record.user_id == self.user_id
        assert audit_record.action == AuditAction.UPDATE
        assert audit_record.target_entity_type == TargetEntity.ALERT
        assert audit_record.target_entity_id == alert.id
        assert audit_record.old_values == {"broadcast": False}
        assert audit_record.new_values == {
            "broadcast": True,
            "neighbourhood_id": str(self.neighbourhood_id),
        }

        # create_audit_log_item commits, then the broadcast service commits.
        assert self.mock_db.commit.await_count == 2
 
    @pytest.mark.asyncio
    async def test_no_residents_still_broadcasts_but_skips_notifications(self):
        alert = self._make_alert()
        camera = self._make_camera()
        neighbourhood = self._make_neighbourhood()

        self.mock_db.execute.side_effect = [
            self._exec_result(scalar_one_or_none=alert),
            self._exec_result(scalar_one_or_none=camera),
            self._admin_membership_result(),
            self._exec_result(scalar_one_or_none=neighbourhood),
            self._exec_result(scalars_all=[]),
        ]
 
        with (
            patch(
                "app.services.alert_service._get_neighbourhood_websocket_recipient_ids", 
                new_callable=AsyncMock,
                return_value=[], 
            ),
            patch("app.api.controllers.alert.broadcast", new_callable=AsyncMock) as mock_broadcast,
            patch("app.services.alert_service._format_whatsapp_message", return_value="msg"),
            patch("app.services.alert_service._notify_users") as mock_notify
        ):
 
            await broadcast_neighbourhood_alert_service(alert.id, self.mock_db, self.claims)
 
        mock_broadcast.assert_awaited_once()
        mock_notify.assert_awaited_once()
        assert mock_notify.call_args.args[2] == []
        # create_audit_log_item commits, then the broadcast service commits.
        assert self.mock_db.commit.await_count == 2