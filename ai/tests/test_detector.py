import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

model = YOLO('ai/pipeline/models/weights/yolov8n.pt')

tracker = DeepSort(
    max_age=70,           # keep lost tracks for 70 frames before deleting
    n_init=2,             # require 2 consecutive detections to confirm a track
    max_iou_distance=0.7,
    embedder="mobilenet", # appearance model for re-identification
    embedder_gpu=True     # set False if no GPU available
)

# original url (stream 1)
# url = "rtsp://Intrepid:password1234@192.168.1.126:554/stream1"

# url with stream 2, to lower resolution stream
url = "rtsp://Intrepid:password1234@192.168.1.126:554/stream2"

cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Failed to open stream")
    exit()

print("Stream opened successfully")

PERSON_CLASS = 0
unique_ids = set()
frame_count = 0

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    frame_count += 1
    if frame_count % 3 != 0:
        continue

    # YOLO detection only (no built-in tracker)
    results = model.predict(
        frame,
        verbose=False,
        conf=0.45,
        iou=0.3,
        imgsz=640,
    )

    # collect person detections for DeepSORT
    detections = []
    for box in results[0].boxes:
        if int(box.cls[0]) == PERSON_CLASS:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            detections.append(([x1, y1, x2 - x1, y2 - y1], confidence, "person"))

    # DeepSORT tracking with appearance re-ID
    tracks = tracker.update_tracks(detections, frame=frame)

    for track in tracks:
        if not track.is_confirmed():
            continue
        track_id = track.track_id
        unique_ids.add(track_id)
        conf = f"{track.det_conf:.2f}" if track.det_conf is not None else "N/A"
        print(f"Track ID: {track_id} --- Confidence: {conf}")

    # 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
print(f"Human Count: {len(unique_ids)}")
print("Done")