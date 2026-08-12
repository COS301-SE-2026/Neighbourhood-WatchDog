# Weapon Detection Candidate 40-Epoch v1 (early-stopped at epoch 28)

- Evaluation images: **89**
- Current model: `data/curated/weapons-gun-knife-v1/training-runs/weapons-gun-knife-40epoch-v1/weights/best.pt`
- Confidence / NMS / match IoU: **0.5 / 0.5 / 0.5**

| Class | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Gun | 0 | 0 | 33 | 0.0000 | 0.0000 | 0.0000 |
| knife | 9 | 1 | 21 | 0.9000 | 0.3000 | 0.4500 |

## Scope

The candidate model uses class 0 for Gun and class 1 for knife. Both outputs are scored against the frozen two-class evaluation set.

## Limitations
- Gun examples are source-separated by scene; knife source grouping is unknown.
- Twenty-five held-out WatchDog hard-negative frames come from one source clip.
- This is a fixed regression evaluation, not a field-performance estimate.
