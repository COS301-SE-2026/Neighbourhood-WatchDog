import logging

import pytest

from app.core.app_logging import RedactTokenFilter, configure_logging

TOKEN = "eyJhbGciOiJSUzI1NiJ9.secret"

def make_record(msg, *args):
    return logging.LogRecord("uvicorn.error", logging.INFO, __file__, 1, msg, args, None)

def test_redacts_token_in_websocket_log_args():
    record = make_record(
        '%s - "WebSocket %s" [accepted]',
        "127.0.0.1:5000",
        f"/api/stream/cameras/abc/annotations/ws?token={TOKEN}",
    )

    assert RedactTokenFilter().filter(record) is True
    message = record.getMessage()
    assert TOKEN not in message
    assert "ws?token=[REDACTED]" in message

def test_keeps_access_log_args_as_a_tuple_of_the_same_length():
    # uvicorn's AccessFormatter unpacks record.args into five values.
    record = make_record(
        '%s - "%s %s HTTP/%s" %d',
        "127.0.0.1:5000", "GET", f"/api/x?a=1&token={TOKEN}&b=2", "1.1", 200,
    )

    RedactTokenFilter().filter(record)

    assert len(record.args) == 5
    assert record.args[2] == "/api/x?a=1&token=[REDACTED]&b=2"
    assert record.args[4] == 200

def test_redacts_token_in_preformatted_message():
    record = make_record(f"GET /alerts/ws?token={TOKEN}")

    RedactTokenFilter().filter(record)

    assert record.getMessage() == "GET /alerts/ws?token=[REDACTED]"

def test_leaves_messages_without_a_token_unchanged():
    record = make_record("camera %s connected", "abc")

    RedactTokenFilter().filter(record)

    assert record.getMessage() == "camera abc connected"

@pytest.mark.parametrize("level", ["info", "DEBUG", "not-a-level"])
def test_configure_logging_attaches_filter_to_uvicorn_loggers(level, monkeypatch):
    for name in ("uvicorn.access", "uvicorn.error"):
        monkeypatch.setattr(logging.getLogger(name), "filters", [])

    configure_logging(level)

    for name in ("uvicorn.access", "uvicorn.error"):
        assert any(isinstance(f, RedactTokenFilter) for f in logging.getLogger(name).filters)
