# Phase 01: Foundation Setup - Research

## Overview

Research for Phase 01: Foundation Setup - setting up project structure, dependencies, and development environment for YOLOv8-based occupancy detection.

## Key Findings

### Project Stack

- **Language:** Python 3.8+
- **Core Framework:** YOLOv8 (Ultralytics)
- **Key Dependencies:** 
  - `ultralytics` - YOLOv8 implementation
  - `opencv-python` - Video processing
  - `numpy` - Numerical operations
  - `torch` - PyTorch backend (for YOLOv8)

### Environment Setup

1. **Python Environment:** Use virtual environment (venv) or conda
2. **Package Management:** pip or poetry
3. **GPU Support:** CUDA for faster inference (optional but recommended)

### Directory Structure

```
watt-watch/
├── data/           # Training data and test clips
├── models/         # Saved YOLOv8 models
├── src/            # Source code
│   ├── detection/  # Detection logic
│   ├── tracking/   # People tracking
│   └── utils/      # Utilities
├── tests/          # Test cases
├── logs/           # FPS and performance logs
└── configs/        # Configuration files
```

### Dependencies to Install

```bash
pip install ultralytics opencv-python numpy torch
# For GPU support:
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Key Considerations

- YOLOv8 can run on CPU but GPU significantly speeds up inference
- OpenCV needed for video frame extraction
- Need to ensure CUDA compatibility for GPU inference

## Technical Notes

- YOLOv8 nano (yolov8n.pt) is smallest/fastest model suitable for real-time
- Model can be loaded via `ultralytics.YOLO('yolov8n.pt')`
- Detection results accessible via `.results[0].boxes`

## Common Pitfalls

- Missing OpenCV ffmpeg dependencies on Linux
- GPU memory issues with larger models
- Python version compatibility (need 3.8+)

## Architecture Patterns

- Use YOLOv8n for real-time, yolov8s for better accuracy
- Class filter: person class (COCO class 0)
- Confidence threshold: 0.25-0.5 for balanced precision/recall

---

**Research completed for Phase 01 Foundation Setup**
**Requirements addressed:** FOUNDATION-01