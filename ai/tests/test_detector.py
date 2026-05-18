import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

from ultralytics import YOLO

model = YOLO('ai/pipeline/models/weights/yolov8n.pt')

#original url (stream 1)
# url = "rtsp://Intrepid:password1234@192.168.1.126:554/stream1"

#url with stream 2, to lower resolution stream
url = "rtsp://Intrepid:password1234@192.168.1.126:554/stream2"


results = model.track(
                # source="ai/tests/footage/clear-presence.mp4", 
                source=url,
                verbose=False, 
                stream=True, 
                conf=0.6, 
                iou=0.3,
                tracker="bytetrack.yaml",
                persist=True,

                #adding these to reduce overhead on cpu
                imgsz=320, 
                vid_stride=3) #processing every third frame to reduce load

PERSON_CLASS = 0
# human_count = 0
unique_ids = set()


for result in results:
    for box in result.boxes:
        if int(box.cls[0]) == PERSON_CLASS and box.id is not None:
            track_id = int(box.id[0])
            confidence = float(box.conf[0])
            unique_ids.add(int(box.id[0]))
            print(f"Track ID: {track_id} --- Confidence: {confidence:.2f}")

print(f"Human Count: {len(unique_ids)}")
print("Done")