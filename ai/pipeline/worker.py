import os
from ai.pipeline.ingestion.ffmpeg_handler import StreamCapture
from ai.pipeline.processing.tracker import Detector

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
# from ai.utils.thumbnail import annotate_frame, encode_frame_as_jpeg

STREAM_URL = "rtsp://Intrepid:password1234@192.168.1.126:554/stream2"
WEIGHTS = "ai/pipeline/models/weights/yolov8n.pt"

def run():
    stream = StreamCapture(STREAM_URL)
    detector = Detector(WEIGHTS, conf=0.6, iou=0.3)

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
                unique_ids.add(track['track_id'])
                print(f"Track ID: {track['track_id']} --- Confidence: {track['confidence']:.2f}")

    except KeyboardInterrupt:
        print("\nStopped")

    finally:
        stream.release()
        print(f"Total unique persons: len{unique_ids}")

if __name__ == "__main__": 
    run()