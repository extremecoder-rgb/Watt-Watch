# Phase 05: Robustness Enhancements - Context

## User Decisions

**Phase Goal:** Handle occlusions, low-light, and motion challenges

**Challenges to Address:**
1. **Occlusion (ROBUST-01):** People blocking each other
   - YOLOv8 handles some occlusion natively
   - Could add tracking to maintain identity across frames
   - Non-maximum suppression tuning

2. **Low-light (ROBUST-02):** Dark environments
   - Image preprocessing (histogram equalization, contrast enhancement)
   - Model inference adjustments
   - May need different confidence thresholds

3. **Motion (ROBUST-03):** Erratic movement
   - Temporal smoothing (average detections over frames)
   - Kalman filtering for tracking
   - Reduce jitter in count changes

**Implementation Note:** These are enhancements to the existing pipeline. The core YOLOv8 detection already handles many cases - these are refinements for edge cases.

**Requirements:** ROBUST-01, ROBUST-02, ROBUST-03

---

## Approach

For each challenge, we have 3 plans:

**Plan 1: Occlusion Handling**
- Track people across frames using centroid matching
- Handle disappearing/reappearing people
- Maintain count consistency

**Plan 2: Low-Light Enhancement**  
- Add preprocessing for dark frames
- Adjust detection thresholds based on brightness
- Log when low-light conditions detected

**Plan 3: Motion Smoothing**
- Apply temporal smoothing to detection counts
- Reduce rapid count fluctuations
- Track historical average