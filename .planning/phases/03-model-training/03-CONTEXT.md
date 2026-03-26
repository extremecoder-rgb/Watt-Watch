# Phase 03: YOLOv8 Model Training - Context

## User Decisions

**Phase Goal:** Train YOLOv8 model for people detection

**Approach:** Use pre-trained YOLOv8 nano model (yolov8n.pt) for inference - no custom training needed. The pre-trained COCO model already detects "person" class (class 0).

**Testing Requirements from Original Context:**
- Test on 3 clips: occupied, empty, quiet-reader
- Log FPS during inference
- Document failure cases

**Note:** For real-time occupancy detection, the pre-trained YOLOv8 model is sufficient. Custom training would only be needed if:
- Specific场景 (特定场景) requires it
- Higher accuracy needed than COCO provides
- Domain-specific person detection (e.g., different camera angles, postures)

---

## Technical Note

YOLOv8 pre-trained on COCO dataset includes "person" class. Using `yolov8n.pt` (nano) provides:
- Fast inference (suitable for real-time)
- Good enough accuracy for occupancy detection
- No training data collection needed

This simplifies Phase 03 significantly - we configure the model for inference rather than training from scratch.