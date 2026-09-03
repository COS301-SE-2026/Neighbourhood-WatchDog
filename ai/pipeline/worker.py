import argparse
import os
from pathlib import Path

from ai.pipeline.ingestion.ffmpeg_handler import StreamCapture
from ai.pipeline.processing.tracker import Detector


def run(stream_url: str, weights_path: Path) -> None:
    stream = StreamCapture(stream_url)
    detector = Detector(str(weights_path), conf=0.6, iou=0.3)

    frame_count = 0
    unique_ids = set()

    print("Pipeline is running")

    try:
        while True:
            frame = stream.read_frame()

            if frame is None:
                print("Empty frame, skipping")
                continue

            frame_count += 1

            if frame_count % 3 != 0:
                continue

            tracks = detector.process_frame(frame)

            for track in tracks:
                unique_ids.add(track["track_id"])
                print(
                    f"Track ID: {track['track_id']} --- "
                    f"Confidence: {track['confidence']:.2f}"
                )

    except KeyboardInterrupt:
        print("\nStopped")

    finally:
        stream.release()
        print(f"Total unique persons: {len(unique_ids)}")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--stream-url",
        default=None,
        help="RTSP URL supplied by configuration",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Path to the detection model",
    )

    args = parser.parse_args()

    stream_url = args.stream_url or os.getenv("WATCHDOG_TEST_RTSP_URL")

    if not stream_url:
        raise SystemExit(
            "No stream configured. Provide --stream-url or "
            "WATCHDOG_TEST_RTSP_URL."
        )

    weights_path = (
        Path(args.model)
        if args.model
        else Path(__file__).resolve().parent
        / "models"
        / "weights"
        / "best.pt"
    )

    run(stream_url, weights_path)


if __name__ == "__main__":
    main()