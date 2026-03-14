# StegXtreme — Model Documentation

## Overview
StegXtreme uses two neural networks for adaptive steganography
and one for network traffic mimicry.

---

## HiderNetwork
**File:** `storage/models/hider.onnx` / `hider_trained.pt`
**Architecture:** Conv2d encoder with Tanh output

### Input
- `cover_Y`: (B, 1, H, W) — Y channel of cover frame
- `payload_bits`: (B, 1, H, W) — bits to embed

### Output
- `residual`: (B, 1, H, W) — add to cover_Y to get stego frame

### How to Use
```python
import onnxruntime as ort
session = ort.InferenceSession("storage/models/hider.onnx")
out = session.run(["residual"], {
    "cover_Y": cover_frame,
    "payload_bits": payload
})
```

### How to Retrain
```bash
python -m core.neural.run_training
```
Runs 200 steps, saves to `storage/models/hider_trained.pt`

---

## DetectorNetwork
**File:** `storage/models/detector.onnx` / `detector_trained.pt`
**Architecture:** Conv2d feature extractor + MLP classifier

### Input
- `frame_Y`: (B, 1, H, W) — Y channel of any frame

### Output
- `probability`: float between 0 and 1
  - 0.0 = clean frame
  - 1.0 = stego frame detected

### Interpretation
- < 0.2 → clean
- 0.2 - 0.7 → uncertain
- > 0.7 → likely stego

---

## TrafficMimicModel
**File:** `storage/models/traffic_mimic.onnx`
**Architecture:** 3-layer MLP with Sigmoid output

### Input
- `recent_delays`: (1, 10) — last 10 inter-packet delays in seconds

### Output
- `next_delay`: float between 0.05s and 2.0s

### How to Retrain
```bash
python -m core.neural.train_traffic
```

---

## Adaptive Training
StegXtreme models improve automatically via `FeedbackEngine`:
- Every embed operation is recorded
- If detection rate exceeds 30%, background retraining triggers
- Models saved to `storage/models/` after each retrain
- Per-installation models — unique to each user's media patterns

---

## Model Signing
All saved models are signed with Ed25519:
- `.pt` file + `.pt.sig` signature file
- Signature verified on load
- Prevents tampered model loading