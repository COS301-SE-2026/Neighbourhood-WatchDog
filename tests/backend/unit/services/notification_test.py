import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

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
    build_alert_email, 
    send_alert_email_bcc, 
    _notify_users_by_bcc_email
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
    @patch("app.services.notification_service.SENDER_EMAIL", "bot@watchdog.com")
    @patch("app.services.notification_service.SENDER_PASSWORD", "pw")
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

    @patch("app.services.notification_service.SENDER_EMAIL", None)
    @patch("app.services.notification_service.SENDER_PASSWORD", None)
    def test_missing_smtp_credentials_returns_failure(self, *_):
        success, error = send_alert_email(
            "resident@example.com", "WEAPON_DETECTED", "CAM 03", "Front Gate", "CRITICAL"
        )

        assert success is False
        assert error == "SMTP credentials not configured"

    @patch("app.services.notification_service.SENDER_EMAIL", "bot@watchdog.com")
    @patch("app.services.notification_service.SENDER_PASSWORD", "pw")
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



class TestBuildAlertEmail:
    def test_escapes_dynamic_content_and_dashboard_url(self):
        body = build_alert_email(
            "<script>alert(1)</script>",
            "CAM <03>",
            "Front & <Gate>",
            'high"priority',
            'https://dashboard.example/alerts?id="quoted"',
        )

        assert "<script>alert(1)</script>" not in body
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
        assert "CAM &lt;03&gt;" in body
        assert "Front &amp; &lt;Gate&gt;" in body
        assert "HIGH&quot;PRIORITY" in body
        assert "&quot;quoted&quot;" in body

    def test_critical_without_dashboard_uses_critical_colour_and_no_cta(self):
        body = build_alert_email(
            "WEAPON_DETECTED",
            "CAM 03",
            "Front Gate",
            "CRITICAL",
            dashboard_url=None,
        )

        assert "background-color: #EF4444" in body
        assert "View alert details" not in body

    def test_unknown_risk_level_uses_safe_fallback_colour(self):
        body = build_alert_email(
            "LOITERING",
            "CAM 03",
            "Front Gate",
            "UNKNOWN",
        )

        assert "background-color: #F59E0B" in body
        assert "UNKNOWN priority" in body


class TestSendAlertEmailBcc:
    def test_empty_recipient_list_returns_failure(self):
        success, error = send_alert_email_bcc(
            [], "WEAPON_DETECTED", "CAM 03", "Front Gate", "CRITICAL"
        )

        assert success is False
        assert error == "No email recipients provided"

    @patch("app.services.notification_service.SENDER_EMAIL", None)
    @patch("app.services.notification_service.SENDER_PASSWORD", None)
    def test_missing_smtp_credentials_returns_failure(self):
        success, error = send_alert_email_bcc(
            ["resident@example.com"],
            "WEAPON_DETECTED",
            "CAM 03",
            "Front Gate",
            "CRITICAL",
        )

        assert success is False
        assert error == "SMTP credentials not configured"

    @patch("app.services.notification_service.SENDER_EMAIL", "bot@watchdog.com")
    @patch("app.services.notification_service.SENDER_PASSWORD", "pw")
    @patch("app.services.notification_service.smtplib.SMTP")
    def test_smtp_exception_returns_failure(self, mock_smtp_cls):
        mock_server = Mock()
        mock_server.sendmail.side_effect = Exception("smtp connection refused")
        mock_smtp_cls.return_value = mock_server

        success, error = send_alert_email_bcc(
            ["resident@example.com"],
            "WEAPON_DETECTED",
            "CAM 03",
            "Front Gate",
            "CRITICAL",
        )

        assert success is False
        assert error == "smtp connection refused"


class TestNotifyUsersBcc:
    def setup_method(self):
        self.mock_db = Mock()
        self.alert_id = uuid.uuid4()
        self.camera = Mock()
        self.camera.name = "CAM 03"
        self.camera.location = "Front Gate"

    def _make_user(self, email):
        user = Mock()
        user.id = uuid.uuid4()
        user.email = email
        user.phone_number = None
        return user

    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch(
        "app.services.notification_service.send_alert_email_bcc",
        side_effect=[(True, None), (False, "smtp error")],
    )
    async def test_bcc_batches_and_logs_each_user_result(self, mock_bcc, mock_log):
        users = [
            self._make_user("one@example.com"),
            self._make_user("two@example.com"),
            self._make_user("three@example.com"),
            self._make_user(None),
        ]

        with patch("app.services.notification_service.MAX_EMAIL_BATCH_SIZE", 2):
            await _notify_users_by_bcc_email(
                self.mock_db,
                self.alert_id,
                users,
                "WEAPON_DETECTED",
                self.camera,
                "CRITICAL",
            )

        assert mock_bcc.call_count == 2
        assert mock_bcc.call_args_list[0].args[0] == [
            "one@example.com",
            "two@example.com",
        ]
        assert mock_bcc.call_args_list[1].args[0] == ["three@example.com"]

        assert mock_log.call_count == 3
        assert mock_log.call_args_list[0].args[3] == NotificationChannel.EMAIL
        assert mock_log.call_args_list[0].args[4] is True
        assert mock_log.call_args_list[1].args[4] is True
        assert mock_log.call_args_list[2].args[4] is False
        assert mock_log.call_args_list[2].args[5] == "smtp error"

    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch("app.services.notification_service.send_alert_email_bcc")
    async def test_bcc_skips_users_without_email(self, mock_bcc, mock_log):
        await _notify_users_by_bcc_email(
            self.mock_db,
            self.alert_id,
            [self._make_user(None)],
            "WEAPON_DETECTED",
            self.camera,
            "CRITICAL",
        )

        mock_bcc.assert_not_called()
        mock_log.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.notification_service._notify_users_by_bcc_email", new_callable=AsyncMock)
    @patch("app.services.notification_service._notify_users_by_whatsapp", new_callable=AsyncMock)
    async def test_notify_users_routes_to_bcc_branch(self, mock_whatsapp, mock_bcc):
        user = self._make_user("resident@example.com")

        await _notify_users(
            self.mock_db,
            self.alert_id,
            [user],
            "message",
            "WEAPON_DETECTED",
            self.camera,
            "CRITICAL",
            email_bcc=True,
        )

        mock_whatsapp.assert_awaited_once_with(
            self.mock_db,
            self.alert_id,
            [user],
            "message",
        )
        mock_bcc.assert_awaited_once_with(
            self.mock_db,
            self.alert_id,
            [user],
            "WEAPON_DETECTED",
            self.camera,
            "CRITICAL",
        )

class TestLogNotification:
    def setup_method(self):
        self.mock_db = Mock()
 
    def test_success_creates_sent_record(self):
        _log_notification(self.mock_db, uuid.uuid4(), uuid.uuid4(), NotificationChannel.WHATSAPP, True, None)
 
        self.mock_db.add.assert_called_once()
        record = self.mock_db.add.call_args.args[0]
        assert record.status == NotificationStatus.SENT
        assert record.error_message is None
        self.mock_db.commit.assert_not_called()
        self.mock_db.rollback.assert_not_called()
 
    def test_failure_creates_failed_record_with_error(self):
        _log_notification(self.mock_db, uuid.uuid4(), uuid.uuid4(), NotificationChannel.WHATSAPP, False, "send failed")

        self.mock_db.add.assert_called_once()
        record = self.mock_db.add.call_args.args[0]
        assert record.status == NotificationStatus.FAILED
        assert record.error_message == "send failed"


class TestDispatchNotifications:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        self.alert_id = uuid.uuid4()
        self.camera_id = uuid.uuid4()
        self.property_id = uuid.uuid4()
        self.neighbourhood_id = uuid.uuid4()
        self.direct_user_id = uuid.uuid4()
        self.frame_timestamp = datetime.now(timezone.utc)

        self.mock_camera = Mock()
        self.mock_camera.id = self.camera_id
        self.mock_camera.name = "CAM 03"
        self.mock_camera.location = "Front Gate"
        self.mock_camera.property_id = self.property_id

    @staticmethod
    def _scalar_result(value):
        result = Mock()
        result.scalar_one_or_none.return_value = value
        return result

    @staticmethod
    def _scalars_result(values):
        result = Mock()
        result.scalars.return_value.all.return_value = values
        return result
 
    def _make_resident(
            self, _id: uuid.UUID | None = None, 
            phone_number: str | None = "0821234567",
            email: str | None = "resident@gmail.com"
    ):
        user = Mock()
        user.id = uuid.uuid4()
        user.phone_number = phone_number
        user.email = email
        return user

    def _configure_high_recipients(self, users):
        """HIGH alerts notify direct users of the camera's property."""
        self.mock_db.execute.side_effect = [
            self._scalar_result(self.mock_camera),
            self._scalar_result(self.neighbourhood_id),
            self._scalars_result(users),
        ]


    def _configure_critical_recipients(
        self,
        direct_users,
        neighbourhood_users,
    ):
        """CRITICAL alerts notify direct users plus neighbourhood residents."""
        self.mock_db.execute.side_effect = [
            self._scalar_result(self.mock_camera),
            self._scalar_result(self.neighbourhood_id),
            self._scalars_result(
                [user.id for user in neighbourhood_users]
            ),
            self._scalars_result(direct_users + neighbourhood_users),
        ]

    @pytest.mark.asyncio
    async def test_below_threshold_skips_entirely(self):
        await dispatch_notifications(
            db=self.mock_db,
            alert_id=self.alert_id,
            camera_id=self.camera_id,
            user_ids=[self.direct_user_id],
            detection_type="LOITERING",
            confidence_score=0.2,
            frame_timestamp=self.frame_timestamp,
        )
        self.mock_db.execute.assert_not_awaited()
        self.mock_db.commit.assert_not_awaited()
 
    @pytest.mark.asyncio
    async def test_notifications_disabled_skips_entirely(self):
        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "false"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[self.direct_user_id],
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )
            self.mock_db.execute.assert_not_awaited()
            self.mock_db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_camera_not_found_returns_early(self):
        self.mock_db.execute.return_value = self._scalar_result(None)

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}), \
             patch("app.services.notification_service._send_whatsapp") as mock_send, \
             patch("app.services.notification_service.send_alert_email") as mock_email:
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[self.direct_user_id],
                detection_type="WEAPON_DETECTED",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )
            mock_send.assert_not_called()
            mock_email.assert_not_called()
            self.mock_db.commit.assert_not_awaited()


    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_critical_type_notifies_neighbourhood_via_both_channels(self, mock_send, mock_email):
        direct_resident = self._make_resident()
        neighbourhood_resident = self._make_resident()

        self._configure_critical_recipients(
            direct_users=[direct_resident],
            neighbourhood_users=[neighbourhood_resident],
        )

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[direct_resident.id],
                detection_type="WEAPON_DETECTED",
                confidence_score=0.1,
                frame_timestamp=self.frame_timestamp,
            )

        assert mock_send.call_count == 2
        assert mock_email.call_count == 2
        self.mock_db.commit.assert_awaited_once()


    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_non_critical_high_confidence_still_notifies_both_channels(self, mock_send, mock_email):
        resident = self._make_resident()
        self._configure_high_recipients([resident])

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[resident.id],
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

        assert mock_send.call_count == 1
        assert mock_email.call_count == 1
        self.mock_db.commit.assert_awaited_once()


    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_notifies_all_direct_property_users_with_phone_numbers(self, mock_send, mock_email):
        residents = [
            self._make_resident(),
            self._make_resident(),
        ]
        self._configure_high_recipients(residents)

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[resident.id for resident in residents],
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

        assert mock_send.call_count == 2
        assert mock_email.call_count == 2


    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_skips_residents_without_phone_number(self, mock_send, mock_email):
        residents = [
            self._make_resident(phone_number=None),
            self._make_resident(),
        ]
        self._configure_high_recipients(residents)

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[resident.id for resident in residents],
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
        residents = [
            self._make_resident(email=None),
            self._make_resident(),
        ]
        self._configure_high_recipients(residents)

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[resident.id for resident in residents],
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

        assert mock_send.call_count == 2
        assert mock_email.call_count == 1


    @pytest.mark.asyncio
    async def test_no_recipients_found_does_not_error(self):
        self.mock_db.execute.side_effect = [
            self._scalar_result(self.mock_camera),
            self._scalar_result(None),
        ]

        with (
            patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}),
            patch(
                "app.services.notification_service._send_whatsapp",
            ) as mock_send,
            patch(
                "app.services.notification_service.send_alert_email",
            ) as mock_email,
        ):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[],
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

        mock_send.assert_not_called()
        mock_email.assert_not_called()
        self.mock_db.commit.assert_not_awaited()


    @pytest.mark.asyncio
    async def test_db_error_fetching_recipients_is_handled(self):
        self.mock_db.execute.side_effect = [
            self._scalar_result(self.mock_camera),
            Exception("db unavailable"),
        ]

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[uuid.uuid4()],
                detection_type="WEAPON_DETECTED",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

        self.mock_db.rollback.assert_awaited_once()


    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(False, "twilio error"))
    async def test_failed_whatsapp_send_is_logged(
        self,
        mock_send,
        mock_email,
        mock_log,
    ):
        resident = self._make_resident(email=None)
        self._configure_high_recipients([resident])

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[resident.id],
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
    async def test_failed_email_send_is_logged(
        self,
        mock_send,
        mock_email,
        mock_log,
    ):
        resident = self._make_resident(phone_number=None)
        self._configure_high_recipients([resident])

        with patch.dict(os.environ, {"NOTIFICATION_ENABLED": "true"}):
            await dispatch_notifications(
                db=self.mock_db,
                alert_id=self.alert_id,
                camera_id=self.camera_id,
                user_ids=[resident.id],
                detection_type="LOITERING",
                confidence_score=0.9,
                frame_timestamp=self.frame_timestamp,
            )

        mock_log.assert_called_once()
        args = mock_log.call_args.args

        assert args[3] == NotificationChannel.EMAIL
        assert args[4] is False
        assert args[5] == "smtp error"

class TestNotifyUsers:
    def setup_method(self):
        self.mock_db = Mock()
        self.alert_id = uuid.uuid4()
        self.camera = Mock()
        self.camera.name = "CAM 03"
        self.camera.location = "Front Gate"
        self.whatsapp_message = "some formatted whatsapp message"

    def _make_user(self, phone_number: str | None = "0821234567", email: str | None = "resident@gmail.com"):
        user = Mock()
        user.id = uuid.uuid4()
        user.phone_number = phone_number
        user.email = email
        return user

    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_user_with_both_channels_gets_both_sends_and_logs(self, mock_send, mock_email, mock_log):
        user = self._make_user()

        await _notify_users(
            self.mock_db, self.alert_id, [user], self.whatsapp_message,
            "LOITERING", self.camera, "HIGH",
        )

        mock_send.assert_called_once_with(user.phone_number, self.whatsapp_message)
        mock_email.assert_called_once_with(user.email, "LOITERING", self.camera.name, self.camera.location, "HIGH")
        assert mock_log.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch("app.services.notification_service.send_alert_email")
    @patch("app.services.notification_service._send_whatsapp")
    async def test_user_with_no_contact_info_skips_both_channels(self, mock_send, mock_email, mock_log):
        user = self._make_user(phone_number=None, email=None)

        await _notify_users(
            self.mock_db, self.alert_id, [user], self.whatsapp_message,
            "LOITERING", self.camera, "HIGH",
        )

        mock_send.assert_not_called()
        mock_email.assert_not_called()
        mock_log.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(False, "twilio error"))
    async def test_whatsapp_failure_still_attempts_email_independently(self, mock_send, mock_email, mock_log):
        user = self._make_user()

        await _notify_users(
            self.mock_db, self.alert_id, [user], self.whatsapp_message,
            "LOITERING", self.camera, "HIGH",
        )

        mock_email.assert_called_once()  
        assert mock_log.call_count == 2
        whatsapp_log_call = mock_log.call_args_list[0]
        assert whatsapp_log_call.args[3] == NotificationChannel.WHATSAPP
        assert whatsapp_log_call.args[4] is False
        assert whatsapp_log_call.args[5] == "twilio error"

    @pytest.mark.asyncio
    @patch("app.services.notification_service._log_notification")
    @patch("app.services.notification_service.send_alert_email", return_value=(True, None))
    @patch("app.services.notification_service._send_whatsapp", return_value=(True, None))
    async def test_multiple_users_processed_independently(self, mock_send, mock_email, mock_log):
        users = [self._make_user(), self._make_user(phone_number=None), self._make_user(email=None)]

        await _notify_users(
            self.mock_db, self.alert_id, users, self.whatsapp_message,
            "LOITERING", self.camera, "HIGH",
        )

        assert mock_send.call_count == 2  
        assert mock_email.call_count == 2  
        assert mock_log.call_count == 4