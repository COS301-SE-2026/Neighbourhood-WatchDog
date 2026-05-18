from ultralytics import YOLO

model = YOLO('ai/pipeline/models/weights/yolov8n.pt')

results = model.track(source="ai/tests/footage/clear-presence.mp4", 
                verbose=False, 
                stream=True, 
                conf=0.6, 
                iou=0.3,
                tracker="bytetrack.yaml",
                persist=True)

PERSON_CLASS = 0
# human_count = 0
unique_ids = set()

# for result in results:
#     for box in result.boxes:
#         if int(box.cls[0]) == PERSON_CLASS:
#             human_count += 1
#             if box.id is not None:
#                 unique_ids.add(int(box.id[0]))
#             print(f"Human detected - confidence: {float(box.conf[0]):.2f}")


for result in results:
    for box in result.boxes:
        if int(box.cls[0]) == PERSON_CLASS and box.id is not None:
            unique_ids.add(int(box.id[0]))

print(f"Human Count: {len(unique_ids)}")
print("Done")