import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import boto3
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

    if not S3_BUCKET_NAME:
        fail("S3_BUCKET_NAME is not configured. Set it in the AI/root .env before running this test.")

    api_key = (keyring.get_password("WatchDog", "api_key") or os.getenv("INTERNAL_API_TOKEN"))

    if not api_key:
        fail("No paired edge-agent key was found. Run the test from the native Windows environment after pairing.")

    timestamp = datetime.now(timezone.utc)
    headers = {"X-Internal-Token": api_key}

    print(f"Backend: {BACKEND_URL}")
    print(f"Bucket: {S3_BUCKET_NAME}")
    print(f"Camera ID: {CAMERA_ID}")

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

    s3_key = (
        f"clips/{CAMERA_ID}/"
        f"{timestamp:%Y/%m/%d}/"
        f"test_weapon_{timestamp:%Y%m%dT%H%M%SZ}.mp4"
    )

    with tempfile.TemporaryDirectory(prefix="watchdog-s3-smoke-") as temp_dir:
        video_path = Path(temp_dir) / "watchdog-test-footage.mp4"
        create_test_h264_video(video_path)

        #  uploading to S3
        print("\n3/4 Uploading test clip to S3...")

        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com"
        )

        s3.upload_file(
            str(video_path),
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": "video/mp4", "ServerSideEncryption": "AES256"},
        )


        uploaded_object = s3.head_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key
        )

        print(
            "S3 upload verified:",
            f"s3://{S3_BUCKET_NAME}/{s3_key}",
        )

        print("Content-Type:", uploaded_object.get("ContentType"))

    #linking the uploaded object to the alert.
    print("\n4/4 Linking test clip to alert...")


    expires_at = timestamp + timedelta(days=CLIP_RETENTION_DAYS)

    patch_response = httpx.patch(
        f"{BACKEND_URL}/internal/alerts/{alert_id}/clip",
        headers=headers,
        json={
            "clip_s3_key": s3_key,
            "clip_expires_at": expires_at.isoformat(),
        },
        timeout=15.0
    )


    print(
        "Clip-link response:",
        patch_response.status_code,
        patch_response.text,
    )


    patch_response.raise_for_status()

    print("\nSUCCESS")
    print("Alert ID:", alert_id)
    print("S3 key:", s3_key)

    print("Open the alert page as an authorised user and review this test clip.")




if __name__ == "__main__":
    main()