import os
from datetime import date, timedelta

from locust import HttpUser, task, between, events
from dotenv import load_dotenv
load_dotenv()


API_KEY = os.environ.get("EDGE_AGENT_TOKEN")
CAMERA_ID = os.environ.get("TEST_CAMERA_ID", "30000000-0000-0000-0000-000000000001")
PROPERTY_ID = os.environ.get("TEST_PROPERTY_ID", "30000000-0000-0000-0000-000000000001")
NEIGHBOURHOOD_ID = os.environ.get("TEST_NEIGHBOURHOOD_ID", "10000000-0000-0000-0000-000000000001")
ALERT_ID = os.environ.get("TEST_ALERT_ID", "80000000-0000-0000-0000-000000000001")
USER_EMAIL = os.environ.get("USER_EMAIL")
USER_PASSWORD = os.environ.get("USER_PASSWORD")

if not API_KEY:
    raise RuntimeError(
        "EDGE_AGENT_TOKEN env var is not set. Export a real, non-revoked edge agent API key "
        "before running this load test again."
    )

if not USER_EMAIL:
    raise RuntimeError(
        "USER_EMAIL env var not set. Export an email address and run this load test again."
    )

if not USER_PASSWORD:
    raise RuntimeError(
        "USER_PASSWORD env var not set. Export the correct password for the user "
        "and run this load test again."
    )

DETECTION_TYPES = ["HUMAN_PRESENCE", "WEAPON"]

_shared_token = None

@events.test_start.add_listener
def _login_once(environment, **kwargs):
    global _shared_token
    import requests
    res = requests.post(
        f"{environment.host}/auth/login", 
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
    )
    res.raise_for_status()
    body = res.json()
    _shared_token = body["data"]["access_token"]
    if not _shared_token:
        raise RuntimeError(f"Login returned no access token: {body}")

class WatchDogUser(HttpUser):
    wait_time = between(1, 5)
    access_token = None
    
    def on_start(self):
        self.access_token = _shared_token

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    @task(1)
    def list_cameras(self):
        self.client.get(f"/camera/property/{PROPERTY_ID}", headers=self.headers)

    @task(3)
    def list_alerts(self):
        self.client.get(
            f"/alerts/{NEIGHBOURHOOD_ID}",
            params={"limit": 20, "offset": 0},
            headers=self.headers,
            name="/alerts/[neighbourhood_id]",
        )

    @task(2)
    def get_clip(self):
        self.client.get(
            f"/api/clips/{ALERT_ID}",
            headers=self.headers,
            name="/api/clips/[alert_id]",
        )

    @task(1)
    def incident_density(self):
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        self.client.get(
            f"/alerts/neighbourhoods/{NEIGHBOURHOOD_ID}/incident-density",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "west": 28.15,
                "south": -25.80,
                "east": 28.30,
                "north": -25.70,
            },
            headers=self.headers,
            name="/alerts/neighbourhoods/[id]/incident-density",
        )