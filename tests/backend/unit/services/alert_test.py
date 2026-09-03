import hashlib
import uuid
from uuid import UUID, uuid4
from datetime import datetime, timezone
from unittest.mock import ANY, AsyncMock, Mock, patch, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.models.alert import Alert, DetectionType
from app.models.audit_log import AuditAction, TargetEntity
from app.models.camera import Camera
from app.models.neighbourhood_user import NeighbourhoodRole
from app.models.user import User
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.alert import TimeIntervalsEnum, TimePeriod
from app.services.alert_service import (
    acknowledge_alert_handler, 
    broadcast_neighbourhood_alert_service, 
    list_alerts_handler, 
    get_response_metrics_handler, 
    get_alert_frequency_metrics_handler,
    get_alert_for_agent,
)
from app.services.notification_service import send_alert_email_bcc

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

    def _make_alert_context(self, alert):
        camera = Mock()

        property_obj = Mock()
        property_obj.id = uuid.uuid4()
        property_obj.neighbourhood_id = self.neighbourhood_id

        neighbourhood_membership = Mock()
        neighbourhood_membership.user_id = self.user_id
        neighbourhood_membership.neighbourhood_id = self.neighbourhood_id
        neighbourhood_membership.role = NeighbourhoodRole.NEIGHBOURHOOD_ADMIN

        property_membership = Mock()
        property_membership.property_id = property_obj.id
        property_membership.user_id = self.user_id
        property_membership.is_admin = False

        return (
            self._exec_result(one_or_none=(alert, camera, property_obj)),
            self._exec_result(scalar_one_or_none=property_membership),
            self._exec_result(scalar_one_or_none=neighbourhood_membership)
        )

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

    def _exec_result(self, scalar_one_or_none=None, one_or_none=None):
        result = Mock()
        result.scalar_one_or_none.return_value = scalar_one_or_none
        result.one_or_none.return_value = one_or_none
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

    @pytest.mark.asyncio
    async def test_non_member_raises_403(self):
        alert = self._make_alert(status="OPEN")

        camera = Mock()

        property_obj = Mock()
        property_obj.id = uuid.uuid4()
        property_obj.neighbourhood_id = self.neighbourhood_id

        self.mock_db.execute.side_effect = [
            self._exec_result(one_or_none=(alert, camera, property_obj)),
            self._exec_result(scalar_one_or_none=None),
            self._exec_result(scalar_one_or_none=None),
        ]

        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(
                alert.id,
                self.mock_db,
                self.claims,
            )

        assert exc.value.status_code == 403
        assert self.mock_db.execute.await_count == 3
        self.mock_db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_alert_not_found_raises_404(self):
        self.mock_db.execute.return_value = self._exec_result(
            one_or_none=None
        )

        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(uuid.uuid4(), self.mock_db, self.claims)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_already_acknowledged_raises_409(self):
        alert = self._make_alert(status="ACKNOWLEDGED")
        
        camera = Mock()

        property_obj = Mock()
        property_obj.id = uuid.uuid4()
        property_obj.neighbourhood_id = self.neighbourhood_id
        self.mock_db.execute.return_value = self._exec_result(
            one_or_none=(alert, camera, property_obj)
        )

        with pytest.raises(HTTPException) as exc:
            await acknowledge_alert_handler(alert.id, self.mock_db, self.claims)

        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_happy_path_acknowledges_alert(self):
        alert = self._make_alert(status="OPEN")

        self.mock_db.execute.side_effect = self._make_alert_context(alert)

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

        self.mock_db.execute.side_effect = self._make_alert_context(alert)

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


    @pytest.mark.asyncio

    async def test_property_admin_can_acknowledge_non_critical_alert(self):

        alert = self._make_alert(status="OPEN")
        alert_result, property_result, neighbourhood_result = self._make_alert_context(alert)
        property_membership = property_result.scalar_one_or_none.return_value
        property_membership.is_admin = True
        neighbourhood_result.scalar_one_or_none.return_value = None

        self.mock_db.execute.side_effect = [
            alert_result, 
            property_result, 
            neighbourhood_result
        ]


        with patch(
            "app.services.alert_service.create_audit_log_item",
            new_callable=AsyncMock,
        ):
            result = await acknowledge_alert_handler(
                alert.id,
                self.mock_db,
                self.claims,
            )

        assert result.status == "ACKNOWLEDGED"
        assert alert.status == "ACKNOWLEDGED"
        assert alert.resolved_by == self.user_id
        self.mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_property_admin_can_acknowledge_property_without_neighbourhood(self):
        """A property administrator can acknowledge when no neighbourhood is assigned."""
        
        alert = self._make_alert(status="OPEN")
        alert_result, property_result, _ = self._make_alert_context(alert)
        property_obj = alert_result.one_or_none.return_value[2]
        property_obj.neighbourhood_id = None
        property_membership = property_result.scalar_one_or_none.return_value
        property_membership.is_admin = True
        self.mock_db.execute.side_effect = [
            alert_result, 
            property_result

        ]

        with patch(
            "app.services.alert_service.create_audit_log_item",
            new_callable=AsyncMock,
        ):
            result = await acknowledge_alert_handler(
                alert.id,
                self.mock_db,
                self.claims,
            )

        assert result.status == "ACKNOWLEDGED"
        assert alert.status == "ACKNOWLEDGED"
        self.mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_integrity_error_rolls_back_acknowledgement(self):
        """A persistence integrity error returns 500 and rolls back the session."""

        alert = self._make_alert(status="OPEN")

        self.mock_db.execute.side_effect = self._make_alert_context(alert)

        integrity_error = IntegrityError(
            "statement",
            {},
            Exception("constraint violation") ,
        )
        with patch(
            "app.services.alert_service.create_audit_log_item",
            new_callable=AsyncMock,
            side_effect=integrity_error, 
        ):
            with pytest.raises(HTTPException) as exc:
                await acknowledge_alert_handler(
                    alert.id,
                    self.mock_db,
                    self.claims , 
                )

        assert exc.value.status_code == 500
        assert exc.value.detail == "Failed to acknowledge alert"
        self.mock_db.commit.assert_not_awaited()
        self.mock_db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_failure_does_not_undo_acknowledgement(self):
        """A WebSocket failure is best-effort and must not undo the database update."""


        alert = self._make_alert(status="OPEN")
        

        self.mock_db.execute.side_effect = self._make_alert_context(alert)


        with (
            patch(
                "app.services.alert_service.create_audit_log_item",
                new_callable=AsyncMock, 
            ),
            patch(
                "app.services.alert_service._get_neighbourhood_websocket_recipient_ids",
                new_callable=AsyncMock,
                return_value=[str(self.user_id)], 
            ),
            patch(
                "app.api.controllers.alert.broadcast",
                new_callable=AsyncMock,
                side_effect=RuntimeError("websocket unavailable"), 
            ) as mock_broadcast,  
            
        ):
            result = await acknowledge_alert_handler(
                alert.id,
                self.mock_db,
                self.claims,  

            )

        assert result.status == "ACKNOWLEDGED"
        assert alert.status == "ACKNOWLEDGED"
        assert alert.resolved_by == self.user_id

        self.mock_db.commit.assert_awaited_once()


        mock_broadcast.assert_awaited_once()



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
            self.mock_db, alert.id, [resident], "msg", alert.detection_type, camera, "CRITICAL", email_bcc=True
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

class TestGetAlertForAgent:
    def setup_method(self):
        self.mock_db = AsyncMock()
        self.mock_db.execute = AsyncMock()

        self.mock_result = MagicMock()

        self.alert_id = str(uuid4())
        self.camera_id = uuid4()

        self.mock_result.scalar_one_or_none.return_value = Alert(
            id=self.alert_id,
            camera_id=self.camera_id,
            frame_timestamp=datetime.now(),
            detection_type=DetectionType.HUMAN_PRESENCE,
            confidence_score=0.60,
            thumbnail_url="fake_url",
            processed=False,
            status="OPEN",
        )

        self.mock_db.execute.return_value = self.mock_result

        key = "1234567890"
        self.mock_credential = EdgeAgentCredential(
            id=uuid4(),
            property_id=uuid4(),
            key_hash=hashlib.sha256(key.encode('utf-8')).hexdigest(),
            created_at=datetime.now(),
        )
        
    @pytest.mark.asyncio
    async def test_happy_path(self):
        result = await get_alert_for_agent(
            self.alert_id,
            self.mock_credential,
            self.mock_db
        )

        assert result.id == self.alert_id
        assert result.camera_id == self.camera_id
        assert self.mock_result.scalar_one_or_none.call_count == 1
        assert self.mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_invalid_alert_id(self):
        with pytest.raises(HTTPException) as exc:
            _ = await get_alert_for_agent(
            "12",
            self.mock_credential,
            self.mock_db
        )

        assert exc.value.status_code == 400 

class TestSendAlertEmailBcc:
    @patch("app.services.notification_service.SENDER_EMAIL", "bot@watchdog.com")
    @patch("app.services.notification_service.SENDER_PASSWORD", "pw")
    @patch("app.services.notification_service.smtplib.SMTP")
    def test_successful_bcc_send(self, mock_smtp_cls):
        mock_server = Mock()
        mock_smtp_cls.return_value = mock_server

        success, error = send_alert_email_bcc(
            [
                "resident1@gmail.com",
                "resident2@gmail.com"
            ],
            "WEAPON_DETECTED",
            "CAM 03",
            "Front Gate",
            "CRITICAL"
        )

        assert success is True
        assert error is None
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

        sendmail_args = mock_server.sendmail.call_args.args

        assert sendmail_args[0] == "bot@watchdog.com"
        assert sendmail_args[1] == [
            "resident1@gmail.com",
            "resident2@gmail.com"
        ]