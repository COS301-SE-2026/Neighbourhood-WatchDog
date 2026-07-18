import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.notification import NotificationRes, ListNotificationRes

def _make_notification_res(**overrides):
    base = {
        "id": uuid.uuid4(),
        "alert_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "channel": "WHATSAPP",
        "status": "SENT",
        "error_message": None,
        "sent_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base

class TestNotificationRes:
    def test_valid_notification(self):
        data = _make_notification_res()
        res = NotificationRes(**data)
 
        assert res.id == data["id"]
        assert res.alert_id == data["alert_id"]
        assert res.user_id == data["user_id"]
        assert res.channel == "WHATSAPP"
        assert res.status == "SENT"
        assert res.sent_at == data["sent_at"]
 
    def test_email_channel_accepted(self):
        res = NotificationRes(**_make_notification_res(channel="EMAIL"))
        assert res.channel == "EMAIL"
 
    def test_failed_status_accepted(self):
        res = NotificationRes(**_make_notification_res(status="FAILED"))
        assert res.status == "FAILED"
 
    def test_missing_id_raises_validation_error(self):
        data = _make_notification_res()
        del data["id"]
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_missing_alert_id_raises_validation_error(self):
        data = _make_notification_res()
        del data["alert_id"]
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_missing_user_id_raises_validation_error(self):
        data = _make_notification_res()
        del data["user_id"]
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_missing_channel_raises_validation_error(self):
        data = _make_notification_res()
        del data["channel"]
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_missing_status_raises_validation_error(self):
        data = _make_notification_res()
        del data["status"]
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_missing_sent_at_raises_validation_error(self):
        data = _make_notification_res()
        del data["sent_at"]
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_invalid_id_raises_validation_error(self):
        data = _make_notification_res(id="not-a-uuid")
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_invalid_alert_id_raises_validation_error(self):
        data = _make_notification_res(alert_id="not-a-uuid")
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_invalid_user_id_raises_validation_error(self):
        data = _make_notification_res(user_id="not-a-uuid")
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_invalid_sent_at_raises_validation_error(self):
        data = _make_notification_res(sent_at="not-a-date")
        with pytest.raises(ValidationError):
            NotificationRes(**data)
 
    def test_from_attributes_config_present(self):
        assert NotificationRes.model_config.get("from_attributes") is True
 
    def test_from_orm_like_object(self):
        """Should validate from an object with matching attributes, not just a dict."""
        class FakeOrmNotification:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
 
        obj = FakeOrmNotification(**_make_notification_res())
        res = NotificationRes.model_validate(obj)
        assert res.channel == "WHATSAPP"

class TestListNotificationRes:
    def test_valid_with_data(self):
        n1 = NotificationRes(**_make_notification_res())
        n2 = NotificationRes(**_make_notification_res(channel="EMAIL"))
        res = ListNotificationRes(status=200, data=[n1, n2])
 
        assert res.status == 200
        assert res.message is None
        assert len(res.data) == 2
 
    def test_data_defaults_to_empty_list(self):
        res = ListNotificationRes(status=200)
        assert res.data == []
 
    def test_message_optional(self):
        res = ListNotificationRes(status=200, message="No notifications found")
        assert res.message == "No notifications found"
 
    def test_missing_status_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ListNotificationRes(data=[])
 
    def test_invalid_nested_data_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ListNotificationRes(status=200, data=[{"channel": "WHATSAPP"}])
 
    def test_data_from_dicts_is_coerced(self):
        """Pydantic should coerce dicts into NotificationRes"""
        res = ListNotificationRes(status=200, data=[_make_notification_res()])
        assert isinstance(res.data[0], NotificationRes)