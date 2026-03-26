# Phase 04: Real-Time Inference Pipeline - Context

## User Decisions

**Phase Goal:** Build real-time processing pipeline with FPS monitoring

**Real-Time Requirements:**
- Process video frames continuously
- Track FPS (frames per second)
- Log detection results
- Handle video files and webcam streams

**Integration with Previous Phases:**
- Uses YOLOv8 model from Phase 03
- Uses video utilities from Phase 02
- Output format for Phase 06 testing

**Performance Targets:**
- Target: >10 FPS for real-time feel
- Log FPS to file for analysis
- Display FPS overlay in live mode

---

## Implementation Approach

The real-time pipeline combines:
1. Video frame capture (from VideoFrameExtractor)
2. YOLOv8 detection (from YOLODetector)  
3. FPS tracking (from FPSCounter)
4. Results logging (from JSONLogger)

All components exist from earlier phases - need to wire them together in main.py and create a proper processing loop.