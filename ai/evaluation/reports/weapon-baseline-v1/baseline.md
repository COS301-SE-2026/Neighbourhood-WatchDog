# Weapon Detection Baseline v1

- Evaluation images: **89**
- Current model: `pipeline/models/weights/best.pt`
- Confidence / NMS / match IoU: **0.5 / 0.5 / 0.5**

| Class | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Gun | 0 | 1 | 33 | 0.0000 | 0.0000 | 0.0000 |
| knife | 0 | 0 | 30 | 0.0000 | 0.0000 | 0.0000 |

## Scope

Only current-model Gun (class 0) and knife (class 3) outputs are scored. Explosion and grenade outputs have no matching ground truth in this two-class dataset and are not treated as Gun/knife false positives.

## Limitations
- Gun examples are source-separated by scene; knife source grouping is unknown.
- Twenty-five held-out WatchDog hard-negative frames come from one source clip.
- This is a fixed regression evaluation, not a field-performance estimate.
