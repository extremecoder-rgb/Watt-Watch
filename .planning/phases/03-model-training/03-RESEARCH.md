# Phase 03: YOLOv8 Model Training - Research

## Overview

Research for Phase 03: Using pre-trained YOLOv8 model for people detection.

## Key Findings

### YOLOv8 Pre-trained Models

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| yolov8n.pt | 6.3MB | Fastest | Good | Real-time, embedded |
| yolov8s.pt | 22.5MB | Fast | Better | General purpose |
| yolov8m.pt | 52MB | Medium | Good | Higher accuracy |
| yolov8l.pt | 87MB | Slow | Very Good | Batch processing |
| yolov8x.pt | 140MB | Slowest | Best | Maximum accuracy |

For real-time occupancy detection: **yolov8n.pt** (nano) is recommended.

### COCO Person Detection

The COCO dataset includes "person" as class ID 0. YOLOv8 pre-trained models can detect people out of the box without any custom training.

**Confidence threshold:** 0.25-0.5 recommended for occupancy detection
- Lower (0.25): More detections, may include false positives
- Higher (0.5): Fewer detections, more confident

### Model Loading in Code

```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Downloads automatically first time

# Inference
results = model(frame, verbose=False)
# Access boxes: results[0].boxes.xyxy, .conf, .cls
```

### GPU Acceleration

If CUDA available:
- Automatic detection and usage
- Significant speedup (5-10x faster)
- Fallback to CPU if no GPU

### No Custom Training Needed

For this project, pre-trained model is sufficient because:
1. COCO "person" class covers occupancy use case
2. Nano model is fast enough for real-time
3. Custom training requires significant labeled data
4. Pre-trained model handles various poses, scales

Custom training would only be needed for:
- Specific environments (特定环境)
- Different camera angles/positions
- Higher accuracy requirements
- Domain-specific variations

## Requirements Addressed

- MODEL-01: YOLOv8 model trained on people detection (via pre-trained COCO)

---

**Research completed for Phase 03 Model Training**