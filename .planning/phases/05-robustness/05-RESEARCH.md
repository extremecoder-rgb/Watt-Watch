# Phase 05: Robustness Enhancements - Research

## Overview

Research for Phase 05: Handling occlusions, low-light, and motion challenges.

## Key Findings

### 1. Occlusion Handling (ROBUST-01)

**Problem:** People blocking each other causes missed detections

**Approaches:**
- **Tracking-based:** Use centroid matching across frames to maintain identity
- **NMS tuning:** Adjust Non-Maximum Suppression threshold
- **Multi-scale detection:** YOLOv8 already does this

**Implementation:** Simple tracker using centroid distance matching
- Track people across frames by matching centroids
- Handle entering/leaving frame
- Maintain stable count

### 2. Low-Light Enhancement (ROBUST-02)

**Problem:** Dark scenes have poor detection accuracy

**Approaches:**
- **Histogram equalization:** Improve contrast
- **Adaptive thresholding:** Adjust confidence based on brightness
- **Frame averaging:** Accumulate frames for better detection

**Implementation:** Preprocessing pipeline
- Convert to grayscale, apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Detect brightness, log when low-light
- Optional: lower confidence threshold for dark frames

### 3. Motion Smoothing (ROBUST-03)

**Problem:** Erratic motion causes count jitter

**Approaches:**
- **Temporal averaging:** Smooth over N frames
- **Kalman filtering:** Predict next position
- **Moving average:** Simple rolling window

**Implementation:** Count smoothing
- Maintain rolling average of last N counts
- Report smoothed count instead of raw
- Reduce rapid fluctuations

## Implementation Strategy

All three enhancements add to the existing pipeline:

1. **src/tracker.py** - People tracking for occlusion handling
2. **src/preprocessing.py** - Low-light image enhancement  
3. **src/smoothing.py** - Motion smoothing

These integrate with main.py detection loop.

## Requirements Addressed

- ROBUST-01: Occlusion handling via tracking
- ROBUST-02: Low-light enhancement via preprocessing
- ROBUST-03: Motion smoothing via temporal averaging

---

**Research completed for Phase 05 Robustness**