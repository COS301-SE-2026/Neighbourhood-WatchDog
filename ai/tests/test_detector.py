import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

import cv2
from ultralytics import YOLO

model = YOLO('ai/pipeline/models/weights/yolov8n.pt')

#original url (stream 1)
# url = "rtsp://Intrepid:password1234@192.168.1.126:554/stream1"

#url with stream 2, to lower resolution stream
url = "rtsp://Intrepid:password1234@192.168.1.126:554/stream2"

cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Failed to open stream")
    exit();

print("Stream opened successfully")



PERSON_CLASS = 0
# human_count = 0
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

    results = model.track(
        # # source="ai/tests/footage/clear-presence.mp4", 
        # source=url,
        # verbose=False, 
        # stream=True, 
        # conf=0.6, 
        # iou=0.3,
        # tracker="bytetrack.yaml",
        # persist=True,

        # #adding these to reduce overhead on cpu
        # imgsz=320, 
        # vid_stride=3   #processing every third frame to reduce load

        frame,
        verbose=False,
        conf=0.6,
        iou=0.3,
        tracker="bytetrack.yaml",
        persist=True,
        
    )


    for box in results[0].boxes:
        if int(box.cls[0]) == PERSON_CLASS and box.id is not None:
            track_id = int(box.id[0])
            confidence = float(box.conf[0])
            unique_ids.add(track_id)

            print(f"Track ID: {track_id} --- Confidence: {confidence:.2f}")


    # 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# for result in results:
#     for box in result.boxes:
#         if int(box.cls[0]) == PERSON_CLASS and box.id is not None:
#             track_id = int(box.id[0])
#             confidence = float(box.conf[0])
#             unique_ids.add(int(box.id[0]))
#             print(f"Track ID: {track_id} --- Confidence: {confidence:.2f}")


cap.release()
print(f"Human Count: {len(unique_ids)}")
print("Done")