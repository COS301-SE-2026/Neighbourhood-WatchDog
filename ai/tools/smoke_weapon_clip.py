import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import cv2
import httpx
import keyring
import numpy as np
from dotenv import load_dotenv


AI_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = AI_DIR.parent

load_dotenv(AI_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")


BACKEND_URL = os.getenv("BACKEND_URL", "https://api.neighbourhoodwatchdog.co.za").rstrip("/")
S3_BUCKET_NAME = (os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_BUCKET_NAME", ""))
AWS_REGION = os.getenv("AWS_REGION", "af-south-1")
CLIP_RETENTION_DAYS = int(os.getenv("CLIP_RETENTION_DAYS", "7"))

CAMERA_ID = os.getenv("TEST_CAMERA_ID", "")


def fail(message: str) -> None:
    raise RuntimeError(message)


def create_test_h264_video(output_path: Path) -> None:
    """generates a short browser compatible test MP4 without a camera"""

    raw_path = output_path.with_name("raw-test-video.mp4")

    width, height = 640, 360
    fps = 25
    duration_seconds = 4

    writer = cv2.VideoWriter(str(raw_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    if not writer.isOpened():
        fail("OpenCV could not create the temporary test video.")

    try:
        for frame_number in range(fps * duration_seconds):
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # just a dark blue background
            frame[:] = (50, 22, 10)

            timestamp = frame_number / fps

            cv2.putText(
                frame,
                "WATCHDOG TEST FOOTAGE",
                (95, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                "Synthetic weapon-alert clip",
                (130, 185),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 220, 255),
                2,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                f"Test timestamp: {timestamp:.1f}s",
                (185, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (190, 190, 190),
                1,
                cv2.LINE_AA
            )

            writer.write(frame)
    finally:
        writer.release()

    #   re encoding to H.264 so the browser footage player can play it
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-movflags",
            "+faststart",
            "-an",
            str(output_path)
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        fail(f"FFmpeg conversion failed:\n{result.stderr}")

    raw_path.unlink(missing_ok=True)



def main() -> None:
    if not CAMERA_ID:
        fail("TEST_CAMERA_ID is required.")

    api_key = (keyring.get_password("WatchDog", "api_key") or os.getenv("INTERNAL_API_TOKEN"))

    if not api_key:
        fail("No paired edge-agent key was found. Run the test from the native Windows environment after pairing.")

    timestamp = datetime.now(timezone.utc)
    headers = {"X-Internal-Token": api_key}

    print(f"Backend: {BACKEND_URL}")
    print(f"Camera ID: {CAMERA_ID}")
    print("Clip storage: backend-owned S3 upload")

    #create a real database alert
    print("\n1/4 Creating test weapon alert...")

    create_response = httpx.post(
        f"{BACKEND_URL}/internal/alerts",
        headers=headers,
        json={
            "camera_id": CAMERA_ID,
            "detection_type": "WEAPON_DETECTED",
            "confidence_score": 0.99,
            "frame_timestamp": timestamp.isoformat()
        },
        timeout=15.0
    )

    print(
        "Create-alert response:",
        create_response.status_code,
        create_response.text,
    )


    create_response.raise_for_status()

    alert_id = create_response.json().get("alert_id")
    if not alert_id:
        fail("Alert endpoint returned success without alert_id.")

    #  generate a local synthetic H.264 test clip
    print("\n2/4 Generating synthetic H.264 MP4...")

    with tempfile.TemporaryDirectory(prefix="watchdog-clip-upload-smoke-") as temp_dir:
        video_path = Path(temp_dir) / "watchdog-test-footage.mp4"
        create_test_h264_video(video_path)

        print("\n3/4 Uploading test clip through backend...")
        with video_path.open("rb") as clip_file:
            upload_response = httpx.post(
                f"{BACKEND_URL}/internal/alerts/{alert_id}/clip",
                headers=headers,
                files={"clip": ("test-weapon.mp4", clip_file, "video/mp4")},
                timeout=30.0,
            )

    print("Backend clip-upload response:", upload_response.status_code, upload_response.text)
    upload_response.raise_for_status()
    clip_metadata = upload_response.json()

    print("\nSUCCESS")
    print("Alert ID:", alert_id)
    print("S3 key:", clip_metadata["clip_s3_key"])

    print("Open the alert page as an authorised user and review this test clip.")




if __name__ == "__main__":
    main()
