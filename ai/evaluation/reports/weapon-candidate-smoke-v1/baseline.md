# Weapon Detection Candidate Smoke Test v1

- Evaluation images: **89**
- Current model: `data/curated/weapons-gun-knife-v1/training-runs/weapons-gun-knife-smoke-v1/weights/best.pt`
- Confidence / NMS / match IoU: **0.5 / 0.5 / 0.5**

| Class | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Gun | 0 | 1 | 33 | 0.0000 | 0.0000 | 0.0000 |
| knife | 6 | 4 | 24 | 0.6000 | 0.2000 | 0.3000 |

## Scope

The candidate model uses class 0 for Gun and class 1 for knife. Both outputs are scored against the frozen two-class evaluation set.

## Limitations
- Gun examples are source-separated by scene; knife source grouping is unknown.
- Twenty-five held-out WatchDog hard-negative frames come from one source clip.
- This is a fixed regression evaluation, not a field-performance estimate.
