# Phase 04: Real-Time Inference Pipeline - Research

## Overview

Research for Phase 04: Building real-time processing pipeline with FPS monitoring.

## Key Findings

### Pipeline Components

All components exist from earlier phases:

| Component | Source | Purpose |
|-----------|--------|---------|
| YOLODetector | Phase 01/03 | People detection |
| FPSCounter | Phase 01 | Track frame rate |
| VideoFrameExtractor | Phase 01 | Read video frames |
| JSONLogger | Phase 01 | Log detection results |

### Real-Time Processing Pattern

```
while frame := extractor.read_frame():
    detections = detector.detect_people(frame)
    fps_counter.update()
    logger.log_frame(...)
```

### FPS Monitoring

- **Current FPS:** Rolling average over last N frames (default 30)
- **Average FPS:** Total frames / elapsed time
- **Logging:** Write to logs/fps.log every N frames

### Integration Points

1. **main.py** - CLI entry point with detect/live/benchmark commands
2. **config.yaml** - Pipeline configuration (frame_skip, log_interval)
3. **output/** - JSON logs of detections

### Performance Considerations

- YOLOv8n ~25 FPS on CPU, ~80 FPS on GPU
- Frame skip option to process every Nth frame (reduce load)
- Video resolution affects speed (640x480 faster than 1920x1080)

## Implementation Strategy

1. Enhance main.py processing loop with proper FPS tracking
2. Ensure logging is consistent across modes
3. Add real-time FPS overlay for live mode
4. Create benchmark script to test on video files

## Requirements Addressed

- INFERENCE-01: Real-time inference with FPS logging

---

**Research completed for Phase 04 Real-Time Inference**