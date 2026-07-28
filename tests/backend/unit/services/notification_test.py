import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
import os

from app.services.notification_service import(
    _classify_severity,
    _format_whatsapp_message,
    _log_notification,
    _send_whatsapp,
    dispatch_notifications,
    should_notify,
    send_alert_email,
    _notify_users,
)
from app.models.notification import NotificationChannel, NotificationStatus

WHATSAPP_TEST_NUMBER = "whatsapp:+27821234567"
class TestClassifySeverity:
    def test_critical_at_upper_boundary(self):
        assert _classify_severity("WEAPON_DETECTED", 1.0) == "CRITICAL"

    def test_critical_at_lower_boundary(self):
        assert _classify_severity("WEAPON_DETECTED", 0.85) == "CRITICAL"

    def test_high_at_upper_boundary(self):
        assert _classify_severity("FALL_DETECTED", 0.85) == "CRITICAL"

    def test_non_critical_type_capped_at_high_not_critical(self):
        assert _classify_severity("HUMAN_PRESENCE", 1.0) == "HIGH"

    def test_high_at_upper_confidence(self):
        assert _classify_severity("LOITERING", 0.99) == "HIGH"

    def test_high_at_lower_boundary(self):
        assert _classify_severity("LOITERING", 0.65) == "HIGH"

    def test_medium_at_upper_boundary(self):
        assert _classify_severity("LOITERING", 0.64) == "MEDIUM"

    def test_medium_at_lower_boundary(self):
        assert _classify_severity("LOITERING", 0.45) == "MEDIUM"

    def test_low_at_upper_boundary(self):
        assert _classify_severity("LOITERING", 0.44) == "LOW"

    def test_low_at_zero(self):
        assert _classify_severity("LOITERING", 0.0) == "LOW"

class TestShouldNotify:
    def test_high_confidence_non_critical_triggers(self):
        assert should_notify("LOITERING", 0.70) is True

    def test_medium_does_not_trigger(self):
        assert should_notify("LOITERING", 0.55) is False

    def test_low_does_not_trigger(self):
        assert should_notify("LOITERING", 0.30) is False

    def test_exact_high_threshold_triggers(self):
        assert should_notify("LOITERING", 0.65) is True

    def test_below_high_threshold_does_not_trigger(self):
        assert should_notify("LOITERING", 0.64) is False

    def test_critical_type_triggers_even_at_low_confidence(self):
        assert should_notify("WEAPON_DETECTED", 0.1) is True

    def test_fall_detected_triggers_even_at_low_confidence(self):
        assert should_notify("FALL_DETECTED", 0.05) is True

class TestFormatWhatsappMessage:
    CAMERA_NAME = "CAM 03"
    TIMESTAMP = "01 Jan 2024, 12:00:00"

    def test_critical_includes_red_emoji(self):
        msg = _format_whatsapp_message("CRITICAL", "HUMAN_PRESENCE", self.CAMERA_NAME, self.TIMESTAMP)
        assert "🔴" in msg

    def test_high_includes_yellow_emoji(self):
        msg = _format_whatsapp_message("HIGH", "LOITERING", self.CAMERA_NAME, self.TIMESTAMP)
        assert "🟡" in msg

    def test_contains_camera_name(self):
        msg = _format_whatsapp_message("HIGH", "LOITERING", self.CAMERA_NAME, self.TIMESTAMP)
        assert self.CAMERA_NAME in msg

    def test_contains_timestamp(self):
        msg = _format_whatsapp_message("HIGH", "LOITERING", self.CAMERA_NAME, self.TIMESTAMP)
        assert self.TIMESTAMP in msg

    def test_detection_type_formatted(self):
        msg = _format_whatsapp_message("CRITICAL", "WEAPON_DETECTED", self.CAMERA_NAME, self.TIMESTAMP)
        assert "Weapon Detected" in msg

    def test_contains_severity_label(self):
        msg = _format_whatsapp_message("CRITICAL", "WEAPON_DETECTED", self.CAMERA_NAME, self.TIMESTAMP)
        assert "CRITICAL" in msg

class TestSendWhatsapp:
    @patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "sid", "TWILIO_AUTH_TOKEN": "token"})
    @patch("twilio.rest.Client")
    def test_successful_send(self, mock_client_cls):
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
 
        success, error = _send_whatsapp("0821234567", "hello")
 
        assert success is True
        assert error is None
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["to"] == WHATSAPP_TEST_NUMBER
 
    @patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "sid", "TWILIO_AUTH_TOKEN": "token"})
    @patch("twilio.rest.Client")
    def test_number_already_has_whatsapp_prefix_untouched(self, mock_client_cls):
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
 
        success, _ = _send_whatsapp(WHATSAPP_TEST_NUMBER, "hello")
 
        assert success is True
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["to"] == WHATSAPP_TEST_NUMBER
 
    @patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "sid", "TWILIO_AUTH_TOKEN": "token"})
    @patch("twilio.rest.Client")
    def test_international_number_with_plus_kept(self, mock_client_cls):
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
 
        success, _ = _send_whatsapp("+447911123456", "hello")
 
        assert success is True
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["to"] == "whatsapp:+447911123456"
 
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_credentials_returns_failure(self):
        success, error = _send_whatsapp("0821234567", "hello")
 
        assert success is False
        assert error == "Twilio credentials not configured"
 
    @patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "sid", "TWILIO_AUTH_TOKEN": "token"})
    @patch("twilio.rest.Client")
    def test_twilio_exception_returns_failure(self, mock_client_cls):
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("network error")
        mock_client_cls.return_value = mock_client
 
        success, error = _send_whatsapp("0821234567", "hello")
 
        assert success is False
        assert error == "network error"

class TestSendAlertEmail:
    @patch.dict(os.environ, {"SMTP_SENDER_EMAIL": "bot@watchdog.com", "SMTP_APP_PASSWORD": "pw"})
    @patch("app.services.notification_service.smtplib.SMTP")
    def test_successful_send_returns_true(self, mock_smtp_cls):
        mock_server = Mock()
        mock_smtp_cls.return_value = mock_server

        success, error = send_alert_email(
            "resident@gmail.com", "WEAPON_DETECTED", "CAM 03", "Front Gate", "CRITICAL"
        )

        assert success is True
        assert error is None
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch.dict(os.environ, {"SMTP_SENDER_EMAIL": "bot@watchdog.com", "SMTP_APP_PASSWORD": "pw"})
    @patch("app.services.notification_service.smtplib.SMTP")
    def test_smtp_exception_returns_failure(self, mock_smtp_cls):
        mock_server = Mock()
        mock_server.sendmail.side_effect = Exception("smtp connection refused")
        mock_smtp_cls.return_value = mock_server

        success, error = send_alert_email(
            "resident@gmail.com", "WEAPON_DETECTED", "CAM 03", "Front Gate", "CRITICAL"
        )

        assert success is False
        assert error == "smtp connection refused"

class TestLogNotification:
    def setup_method(self):
        self.mock_db = Mock()
 
    def test_success_creates_sent_record(self):
        _log_notification(self.mock_db, uuid.uuid4(), uuid.uuid4(), NotificationChannel.WHATSAPP, True, None)
 
        self.mock_db.add.assert_called_once()
        record = self.mock_db.add.call_args.args[0]
        assert record.status == NotificationStatus.SENT.value
        assert record.error_message is None
        self.mock_db.commit.assert_called_once()
 
    def test_failure_creates_failed_record_with_error(self):
        _log_notification(self.mock_db, uuid.uuid4(), uuid.uuid4(), NotificationChannel.WHATSAPP, False, "send failed")
 
        record = self.mock_db.add.call_args.args[0]
        assert record.status == NotificationStatus.FAILED.value
        assert record.error_message == "send failed"
 
    def test_db_error_rolls_back_and_does_not_raise(self):
        self.mock_db.commit.side_effect = Exception("db down")
 
        _log_notification(self.mock_db, uuid.uuid4(), uuid.uuid4(), NotificationChannel.WHATSAPP, True, None)
 
        self.mock_db.rollback.assert_called_once()

class TestDispatchNotifications:
    def setup_method(self):
        self.mock_db = Mock()
        self.alert_id = uuid.uuid4()
        self.camera_id = uuid.uuid4()
        self.neighbourhood_id = uuid.uuid4()
        self.frame_timestamp = datetime.now(timezone.utc)

        self.mock_camera = Mock()
        self.mock_camera.name = "CAM 03"
        self.mock_camera.location = "Front Gate"
        self.mock_camera.property_id = uuid.uuid4()
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = self.mock_camera
 
    def _make_resident(self, phone_number="0821234567", email="resident@gmail.com"):
        user = Mock()
        user.id = uuid.uuid4()
        user.phone_number = phone_number
        user.email = email
        return user

    def _set_recipients(self, users):
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = users
 
    @pytest.mark.asyncio
    async def test_below_threshold_skips_entirely(self):
        await dispatch_notifications(
            db=self.mock_db,
            alert_id=self.alert_id,
            camera_id=self.camera_id,
            neighbourhood_id=self.neighbourhood_id,
            detection_type="LOITERING",
            confidence_score=0.2,
            frame_timestamp=self.frame_timestamp,
        )
        self.mock_db.execute.assert_not_called()
 
    @pytest.mark.asyncio
    async def test_notifications_disabled_skips(self):
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "false"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )
            self.mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_camera_not_found_returns_early(self):
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}), \
             patch("app.services.notification_service._send_whatsapp") as mock_send, \
             patch("app.services.notification_service.send_alert_email") as mock_email:
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="WEAPON_DETECTED",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )
            mock_send.assert_not_called()
            mock_email.assert_not_called()


    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_critical_type_notifies_neighbourhood_via_both_channels(self, mock_send, mock_email):
        residents = [self._make_resident(), self._make_resident()]
        self._set_recipients(residents)
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="WEAPON_DETECTED",
                confidence_score=0.1,
                frame_timestamp=self.frame_timestamp,
            )

            assert mock_send.call_count == 2
            assert mock_email.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_non_critical_high_confidence_still_notifies_both_channels(self, mock_send, mock_email):
        residents = [self._make_resident()]
        self._set_recipients(residents)
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

            assert mock_send.call_count == 1
            assert mock_email.call_count == 1
 
    @pytest.mark.asyncio
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_notifies_all_residents_with_phone_numbers(self, mock_send):
        residents = [self._make_resident(), self._make_resident()]
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = residents
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )
    
            assert mock_send.call_count == 2
 
    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_skips_residents_without_phone_number(self, mock_send, mock_email):
        residents = [self._make_resident(phone_number=None), self._make_resident()]
        self._set_recipients(residents)

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

            assert mock_send.call_count == 1  
            assert mock_email.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_skips_residents_without_email(self, mock_send, mock_email):
        residents = [self._make_resident(email=None), self._make_resident()]
        self._set_recipients(residents)

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

            assert mock_send.call_count == 2 
            assert mock_email.call_count == 1 
 
    @pytest.mark.asyncio
    async def test_no_residents_found_does_not_error(self):
        self._set_recipients([])
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}), \
             patch("app.services.notification_service._send_whatsapp") as mock_send, \
             patch("app.services.notification_service.send_alert_email") as mock_email:
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )
            mock_send.assert_not_called()
            mock_email.assert_not_called()
 
    @pytest.mark.asyncio
    async def test_db_error_fetching_residents_is_handled(self):
        self.mock_db.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=self.mock_camera)),
            Exception("db unavailable"),
        ]
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="WEAPON_DETECTED",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(False, "twilio error"))
    async def test_failed_whatsapp_send_is_logged(self, mock_send, mock_email, mock_log):
        residents = [self._make_resident(email=None)]
        self._set_recipients(residents)
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

            mock_log.assert_called_once()
            args = mock_log.call_args.args
            assert args[3] == NotificationChannel.WHATSAPP
            assert args[4] is False
            assert args[5] == "twilio error"
 
    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch("app.services.notification_service.send_alert_email", return_value=(False, "smtp error"))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_failed_email_send_is_logged(self, mock_send, mock_email, mock_log):
        residents = [self._make_resident(phone_number=None)]
        self._set_recipients(residents)
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                neighbourhood_id=self.neighbourhood_id,
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

            mock_log.assert_called_once()
            args = mock_log.call_args.args
            assert args[3] == NotificationChannel.EMAIL
            assert args[4] is False
            assert args[5] == "smtp error"