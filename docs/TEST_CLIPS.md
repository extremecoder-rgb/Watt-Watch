# Test Clips Requirements

This document describes the video test clips needed for Phase 06 Testing and Validation.

## Overview

Three test clips are required to properly evaluate the occupancy detection system:

| Clip | Filename | Purpose |
|------|----------|---------|
| Multi-person | `occupied.mp4` | Test occlusion handling |
| Empty | `empty.mp4` | Test false positive rate |
| Quiet reader | `quiet-reader.mp4` | Test low-motion detection |

---

## Clip Specifications

### 1. occupied.mp4

**Purpose:** Test detection with multiple people and occlusions

**Characteristics:**
- Duration: 30-60 seconds
- People: 3-10 individuals
- Motion: Various (walking, sitting, standing)
- Occlusions: Some people partially blocking others

**Expected Behavior:**
- Should detect multiple people in most frames
- May have some missed detections during heavy occlusions
- Should track consistent count changes

**Acquisition:**
- Record in office/public space with multiple people
- Or use stock video of crowds/groups

---

### 2. empty.mp4

**Purpose:** Test false positive rate, establish baseline

**Characteristics:**
- Duration: 30-60 seconds
- People: 0 (none)
- Scene: Empty office/corridor/room
- Motion: None (static background)

**Expected Behavior:**
- Should detect 0 people in all frames
- Any detections are false positives
- Use to measure false positive rate

**Acquisition:**
- Record empty room/corridor
- Ensure no people in frame

---

### 3. quiet-reader.mp4

**Purpose:** Test single-person detection in low-motion scenario

**Characteristics:**
- Duration: 30-60 seconds
- People: 1 individual
- Activity: Sitting still, reading or using computer
- Motion: Minimal (occasional small movements)

**Expected Behavior:**
- Should consistently detect single person
- Handle cases where person is mostly still
- Test stability of detection over time

**Acquisition:**
- Record single person sitting at desk
- Focus on minimal movement scenarios

---

## Technical Requirements

| Property | Minimum | Recommended |
|----------|---------|-------------|
| Resolution | 640x480 | 1280x720 or higher |
| FPS | 24 | 25-30 |
| Format | MP4 | MP4 (H.264) |
| Codec | H.264 | H.264 |

---

## How to Obtain Test Clips

### Option 1: Record Yourself

Use webcam or phone to record short clips:
- Ensure good lighting
- Stable camera position
- Follow the scene descriptions above

### Option 2: Use Stock Videos

Download from stock video sites:
- Pexels (free)
- Pixabay (free)
- Videvo (free with attribution)

Search terms: "office", "empty room", "reading", "people walking"

### Option 3: Use Sample Datasets

Some detection datasets include videos:
- MOT17 (pedestrian tracking)
- UCSD Pedestrian Dataset

---

## Expected Test Results

### Occupied Clip

| Metric | Target |
|--------|--------|
| Detection rate | >90% of frames have correct count |
| Occlusion handling | Detect at least 80% of people even when occluded |
| False negatives | <10% |

### Empty Clip

| Metric | Target |
|--------|--------|
| False positives | <1% of frames |
| Zero detections | >99% of frames |

### Quiet-Reader Clip

| Metric | Target |
|--------|--------|
| Detection consistency | >95% of frames detect person |
| Stability | <5% variation in count |

---

## Notes

- Placeholder files exist in `data/clips/` - replace with actual videos
- Ensure videos match technical specifications
- Document any specific characteristics of your test clips
- Store original files - don't modify for testing