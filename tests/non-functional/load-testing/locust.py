"""
Locust load test for POST /internal/alerts (the endpoint for edge agent alert creation)
"""

import os

from locust import HttpUser, task, between

API_KEY = os.environ.get("EDGE_AGENT_TOKEN")
CAMERA_ID = os.environ.get("TEST_CAMERA_ID", "40000000-0000-0000-0000-000000000001")
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

class WatchDogUser(HttpUser):
    wait_time = between(0.5, 2)
    access_token = None
    
    def on_start(self):
        payload = {
            "email": USER_EMAIL,
            "password": USER_PASSWORD,
        }

        resp = self.client.post(
            '/auth/login',
            json=payload)

        self.access_token = resp.json().get("access_token")

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    @task(3)
    def list_properties(self):
        self.client.get("/properties/my-properties", headers=self.headers)

    @task(2)
    def list_cameras(self):
        self.client.get("/cameras", headers=self.headers)

    @task(1)
    def list_detections(self):
        self.client.get("/detections", headers=self.headers)

    # @task
    # def create_alert(self):
    #     payload = {
    #         "camera_id": CAMERA_ID,
    #         "detection_type": "HUMAN_PRESENCE",
    #         "confidence_score": round(random.uniform(0.55, 0.99), 2),
    #         "thumbnail_url": None,
    #         "frame_timestamp": datetime.now(timezone.utc).isoformat(),
    #     }
    #     with self.client.post(
    #         "/internal/alerts",
    #         json=payload,
    #         headers=self.headers,
    #         catch_response=True,
    #     ) as response:
    #         if response.status_code == 201:
    #             response.success()
    #         elif response.status_code == 400:
    #             response.failure(f"400 Bad Request: {response.text}")
    #         elif response.status_code == 401:
    #             response.failure(f"401: EDGE_AGENT_TOKEN is invalid or revoked")
    #         elif response.status_code == 404:
    #             response.failure(f"404: camera_id {CAMERA_ID} not found")
    #         else:
    #             response.failure(f"Unexpected status {response.status_code}: {response.text}")
