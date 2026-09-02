# WatchDog Detection Baseline v1

- **Run date:** 2026-08-09T16:54:13.195725+00:00
- **Evaluation frames/images:** 24
- **IoU match threshold:** 0.5
- **Person model:** `pipeline/models/weights/yolov8n.pt` (confidence `0.25`)
- **Threat model:** `pipeline/models/weights/best.pt` (confidence `0.5`)

## Metrics

| Class | TP | FP | FN | Precision | Recall | F1 | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| person | 29 | 1 | 1 | 0.9667 | 0.9667 | 0.9667 | measurable |
| Gun | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |
| explosion | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |
| grenade | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |
| knife | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |
| weapon | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |

## Interpretation

This is an offline, fixed-dataset raw-detection baseline. It excludes DeepSort, zones, alert cooldowns, API calls and alert creation.
A class with no human-labelled positive objects is marked **not measurable** for recall/F1; do not treat a zero value as a model result.
