# Phase 02: Data Preparation - Research

## Overview

Research for Phase 02: Data Preparation - preparing training/validation data and video test clips for evaluation.

## Key Findings

### Test Clip Requirements

For Phase 06 Testing and Validation, we need 3 distinct video clips:

1. **occupied.mp4** - Multiple people, some overlap (tests occlusion handling)
   - Duration: 30-60 seconds
   -场景: Office with 3-10 people moving around
   - Purpose: Test multi-person detection and occlusion handling

2. **empty.mp4** - No people, background only (baseline/negative case)
   - Duration: 30-60 seconds
   -场景: Empty office/corridor
   - Purpose: Verify false positive rate, establish baseline

3. **quiet-reader.mp4** - Single person, still, reading (quiet scene)
   - Duration: 30-60 seconds
   -场景: Single person sitting still, reading
   - Purpose: Test single-person detection, low motion scenarios

### Data Acquisition Options

1. **Sample Videos from ULtralytics**
   - Use YOLOv8 sample videos for initial testing
   - Download from: https://github.com/ultralytics/ultralytics

2. **Custom Recording**
   - Record using webcam or phone
   - Edit to create specific scenarios

3. **Synthetic Data**
   - Use video datasets like MOT17, Penn-Fudan
   - Not ideal for occupancy detection

### Video Specifications

| Property | Recommended |
|----------|--------------|
| Resolution | 1280x720 or higher |
| FPS | 25-30 |
| Format | MP4 (H.264) |
| Codec | libx264 |

### Directory Structure

```
data/
├── clips/              # Test video clips
│   ├── occupied.mp4
│   ├── empty.mp4
│   └── quiet-reader.mp4
├── raw/                # Raw video for processing
├── processed/          # Preprocessed frames
└── annotations/        # Ground truth labels (if needed)
```

### Preprocessing Pipeline

1. **Frame Extraction**
   - Extract frames at specified intervals
   - Store as JPEG for efficiency

2. **Quality Check**
   - Validate video integrity
   - Check resolution, FPS, duration

3. **Metadata Generation**
   - Create video_info.json with properties
   - Log frame count, duration, FPS

### Implementation Approach

Since obtaining real test clips requires manual recording/procurement, the plan should:
1. Create data directory structure
2. Create placeholder videos or use sample videos
3. Implement video validation and preprocessing scripts
4. Document requirements for test clips

## Requirements Addressed

- DATA-01: Video clips (occupied, empty, quiet-reader) prepared

---

**Research completed for Phase 02 Data Preparation**