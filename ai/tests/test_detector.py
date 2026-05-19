import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

model = YOLO('ai/pipeline/models/weights/yolov8n.pt')

tracker = DeepSort(
    max_age=70,           # keep lost tracks for 30 frames before deleting
    n_init=2,             # require 2 consecutive detections to confirm a track
    max_iou_distance=0.7,
    embedder="mobilenet", # appearance model for re-identification
    embedder_gpu=True     # set False if no GPU available
)

#original url (stream 1)
# url = "rtsp://Intrepid:password1234@192.168.1.126:554/stream1"

#url with stream 2, to lower resolution stream
url = "rtsp://Intrepid:password1234@192.168.1.126:554/stream2"


results = model.predict(
                #source="ai/tests/footage/blurred-presence.mp4", 
                source=url,
                verbose=False, 
                stream=True, 
                conf=0.45, 
                iou=0.3,
                #tracker="bytetrack.yaml",
                #persist=True,

                #adding these to reduce overhead on cpu
                imgsz=640, 
                vid_stride=3) #processing every third frame to reduce load

PERSON_CLASS = 0
# human_count = 0
unique_ids = set()


for result in results:
    detections = []
    for box in result.boxes:
        if int(box.cls[0]) == PERSON_CLASS:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            detections.append(([x1, y1, x2 - x1, y2 - y1], confidence, "person"))

    tracks = tracker.update_tracks(detections, frame=result.orig_img)


    for track in tracks:
        if not track.is_confirmed():
            continue
        track_id = track.track_id
        unique_ids.add(track_id)
        conf = f"{track.det_conf:.2f}" if track.det_conf is not None else "N/A"
        print(f"Track ID: {track_id} --- Confidence: {conf}")

print(f"Human Count: {len(unique_ids)}")
print("Done")