# WatchDog Detection Baseline v1

- **Run date:** 2026-09-25T21:08:33.106544+00:00
- **Evaluation frames/images:** 24
- **IoU match threshold:** 0.5
- **Person model:** `pipeline/models/weights/yolov8n.pt` (confidence `0.25`)
- **Threat model:** `pipeline/models/weights/best.pt` (confidence `0.35`)

## Metrics

| Class | TP | FP | FN | Precision | Recall | F1 | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| person | 30 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | measurable |
| Gun | 0 | 2 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |
| explosion | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |
| grenade | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |
| knife | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |
| weapon | 0 | 2 | 0 | 0.0000 | 0.0000 | 0.0000 | not_measurable_no_ground_truth_positive |

## Interpretation

This is an offline, fixed-dataset raw-detection baseline. It excludes DeepSort, zones, alert cooldowns, API calls and alert creation.
A class with no human-labelled positive objects is marked **not measurable** for recall/F1; do not treat a zero value as a model result.
