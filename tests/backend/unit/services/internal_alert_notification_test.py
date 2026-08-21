import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.schemas.alert import CreateInternalAlertRequest
from app.services.alert_service import create_alert_for_agent_handler


class TestInternalAlertNotifications:
    @pytest.mark.asyncio

    async def test_agent_alert_dispatches_notifications_to_property_users():

        camera_id = uuid.uuid4()
        property_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]

        db = Mock()
        db.execute = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()


        camera = Mock(id=camera_id, property_id=property_id)

        camera_result = Mock()
        camera_result.scalar_one_or_none.return_value = camera

        recipients_result = Mock()
        recipients_result.scalars.return_value.all.return_value = user_ids

        db.execute.side_effect = [camera_result, recipients_result]

        alert = Mock(id=uuid.uuid4(), camera_id=camera_id)
        credential = Mock(property_id=property_id)

        body = CreateInternalAlertRequest(
            camera_id=str(camera_id),
            detection_type="WEAPON_DETECTED",
            confidence_score=0.91,
            frame_timestamp="2026-08-21T17:00:00+00:00"
        )

        with (
            patch(
                "app.services.alert_service.Alert",
                return_value=alert
            ),
            patch(
                "app.services.alert_service.dispatch_notifications",
                new_callable=AsyncMock
            ) as dispatch,
        ):
            result = await create_alert_for_agent_handler(
                body,
                db,
                credential
            )



        assert result.alert_id == alert.id

        dispatch.assert_awaited_once()
        kwargs = dispatch.await_args.kwargs


        assert kwargs["db"] is db
        assert kwargs["alert_id"] == alert.id
        assert kwargs["camera_id"] == camera_id
        assert set(kwargs["user_ids"]) == set(user_ids)
        assert kwargs["detection_type"] == "WEAPON_DETECTED"
        assert kwargs["confidence_score"] == 0.91
        assert kwargs["frame_timestamp"] == datetime(2026, 8, 21, 17, 0, tzinfo=timezone.utc)