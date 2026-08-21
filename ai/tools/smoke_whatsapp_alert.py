#!/usr/bin/env python3
"""Run an opt in live WhatsApp alert path smoke test."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import keyring
from dotenv import load_dotenv
from twilio.rest import Client


ROOT = Path(__file__).resolve().parents[2]

load_dotenv(ROOT / "ai" / ".env")
load_dotenv(ROOT / "backend" / ".env", override=False)
load_dotenv(ROOT / ".env", override=False)

BACKEND_URL = os.getenv("BACKEND_URL", "https://api.neighbourhoodwatchdog.co.za").rstrip("/")

CAMERA_ID = os.getenv("WHATSAPP_SMOKE_TEST_CAMERA_ID", "")
TEST_RECIPIENT = os.getenv("WHATSAPP_SMOKE_TEST_RECIPIENT", "")
TIMEOUT_SECONDS = int(os.getenv("WHATSAPP_SMOKE_TIMEOUT_SECONDS", "90"))
POLL_SECONDS = float(os.getenv("WHATSAPP_SMOKE_POLL_SECONDS", "5"))

TERMINAL_FAILURE_STATUSES = {
    "failed",
    "undelivered",
    "canceled"
}


def fail(message: str) -> None:
    print(f"FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


def normalise_whatsapp_number(value: str) -> str:
    value = value.strip()

    if value.startswith("whatsapp:"):
        return value

    if value.startswith("0"):
        value = "+27" + value[1:]

    if not value.startswith("+"):
        value = "+" + value


    return f"whatsapp:{value}"


def get_agent_key() -> str | None:
    try:
        paired_key = keyring.get_password("WatchDog", "api_key")

    except Exception as error:
        print(
            f"Keyring unavailable ({error.__class__.__name__}); "
            "checking TEST_AGENT_API_KEY."
        )

        paired_key = None

    return paired_key or os.getenv("TEST_AGENT_API_KEY")


def latest_matching_message(client: Client, recipient: str, started_at: datetime):

    messages = client.messages.list(to=recipient, limit=20)

    for message in messages:
        sent_at = message.date_sent or message.date_created

        if (sent_at and sent_at.astimezone(timezone.utc) >= started_at):

            body = message.body or ""

            if ("Weapon Detected" in body and "Neighbourhood Watchdog" in body):
                return message

    return None


def main() -> None:
    if os.getenv("ALLOW_LIVE_WHATSAPP_SMOKE") != "true":

        fail(
            "Set ALLOW_LIVE_WHATSAPP_SMOKE=true "
            "to permit a real WhatsApp message."
        )

    if not CAMERA_ID:
        fail("WHATSAPP_SMOKE_TEST_CAMERA_ID is required.")

    if not TEST_RECIPIENT:
        fail("WHATSAPP_SMOKE_TEST_RECIPIENT is required.")



    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        fail(
            "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are required "
            "to verify delivery."
        )

    agent_key = get_agent_key()


    if not agent_key:
        fail(
            "No paired edge-agent key found. Pair natively or set "
            "TEST_AGENT_API_KEY for this one run."
        )

    recipient = normalise_whatsapp_number(TEST_RECIPIENT)
    started_at = datetime.now(timezone.utc)


    print(f"Backend: {BACKEND_URL}")
    print(f"Test camera: {CAMERA_ID}")
    print(f"Expected recipient: {recipient}")
    print("Creating a live test weapon alert through the Edge Agent endpoint...")

    response = httpx.post(
        f"{BACKEND_URL}/internal/alerts",
        headers={"X-Internal-Token": agent_key},
        json={
            "camera_id": CAMERA_ID,
            "detection_type": "WEAPON_DETECTED",
            "confidence_score": 0.99,
            "frame_timestamp": started_at.isoformat()
        },
        timeout=20.0

    )

    response.raise_for_status()

    alert_id = response.json().get("alert_id")

    if not alert_id:
        fail("Alert endpoint returned success without alert_id.")


    client = Client(account_sid, auth_token)
    deadline = time.monotonic() + TIMEOUT_SECONDS
    last_status = "not found"

    while time.monotonic() < deadline:

        message = latest_matching_message(
            client,
            recipient,
            started_at

        )


        if message:
            last_status = (message.status or "unknown").lower()

            print(
                f"Twilio message SID: {message.sid}; "
                f"status: {last_status}"
            )


            if last_status == "delivered":
                print(
                    f"SUCCESS: alert {alert_id} reached {recipient} "
                    "with Twilio delivery status delivered."
                )
                return
            

            if last_status in TERMINAL_FAILURE_STATUSES:
                fail(
                    f"Alert {alert_id} reached Twilio but ended in "
                    f"terminal status {last_status} "
                    f"(SID {message.sid})."
                )


        time.sleep(POLL_SECONDS)


    fail(
        f"Alert {alert_id} was not delivered within "
        f"{TIMEOUT_SECONDS}s (last status: {last_status})."
    )





if __name__ == "__main__":
    main()