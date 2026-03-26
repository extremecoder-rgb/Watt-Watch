# WattWatch Roadmap

## Project: Intelligent Occupancy Detection System

**Goal:** Develop a YOLOv8-based real-time people counting system for video feeds with robust handling of occlusions, low-light, and erratic motion.

---

### Phase 01: Foundation Setup

**Goal:** Set up project structure, dependencies, and development environment

**Status:** ✓ Complete

**Plans:** [x] 01-PLAN.md — Project scaffolding and dependencies

**Requirements:** [FOUNDATION-01]

---

### Phase 02: Data Preparation

**Goal:** Prepare training/validation data and video test clips for evaluation

**Status:** ✓ Complete

**Plans:** [x] 01-PLAN.md — Data collection and preprocessing

**Requirements:** [DATA-01]

---

### Phase 03: YOLOv8 Model Training

**Goal:** Train YOLOv8 model for people detection

**Status:** ✓ Complete

**Plans:** [x] 01-PLAN.md — Model configuration and training

**Requirements:** [MODEL-01]

---

### Phase 04: Real-Time Inference Pipeline

**Goal:** Build real-time processing pipeline with FPS monitoring

**Status:** ✓ Complete

**Plans:** [x] 01-PLAN.md — Inference engine and FPS tracking

**Requirements:** [INFERENCE-01]

---

### Phase 05: Robustness Enhancements

**Goal:** Handle occlusions, low-light, and motion challenges

**Status:** ✓ Complete

**Plans:** [x] 01-PLAN.md — Occlusion handling
[x] 02-PLAN.md — Low-light enhancement
[x] 03-PLAN.md — Motion smoothing

**Requirements:** [ROBUST-01, ROBUST-02, ROBUST-03]

---

### Phase 06: Testing and Validation

**Goal:** Test on 3 clips (occupied, empty, quiet-reader) and document failure cases

**Status:** ○ Pending

**Plans:** [ ] 01-PLAN.md — Evaluation on test clips

**Requirements:** [TEST-01]

---

### Phase 07: Optimization

**Goal:** Optimize compute load and real-time performance

**Status:** ○ Pending

**Plans:** [ ] 01-PLAN.md — Performance optimization

**Requirements:** [OPT-01]

---

### Phase 08: Appliance Status Recognition

**Goal:** Identify projector/monitor/light and classify ON/OFF via pixel brightness

**Status:** ○ Pending

**Plans:** [ ] 01-PLAN.md — Appliance detection and status classification

**Requirements:** [APPLIANCE-01]

---

## Requirements

| ID | Description |
|----|--------------|
| FOUNDATION-01 | Project setup with Python, YOLOv8, and dependencies |
| DATA-01 | Video clips (occupied, empty, quiet-reader) prepared |
| MODEL-01 | YOLOv8 model trained on people detection |
| INFERENCE-01 | Real-time inference with FPS logging |
| ROBUST-01 | Handle occlusions (people blocking each other) |
| ROBUST-02 | Handle low-light conditions |
| ROBUST-03 | Handle erratic motion |
| TEST-01 | Test on 3 clips, log FPS, document failures |
| OPT-01 | Optimize compute load for real-time performance |
| APPLIANCE-01 | Detect appliance type and classify ON/OFF via brightness |

---

## Notes

- Phase "Intelligent Occupancy Detection" from original context spans phases 01-07
- Each test clip should have distinct characteristics:
  - **Occupied:** Multiple people, some overlap
  - **Empty:** No people, background only
  - **Quiet-reader:** Single person, still, reading