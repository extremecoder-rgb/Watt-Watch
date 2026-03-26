---
phase: 03-model-training
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [src/detector.py, config.yaml, models/.gitkeep, tests/test_model.py]
autonomous: true
requirements: [MODEL-01]
must_haves:
  truths:
    - "YOLOv8 model can be loaded and runs inference"
    - "Person detection works on sample frames"
    - "Model configuration is optimized for real-time"
    - "GPU acceleration works if available"
  artifacts:
    - path: "src/detector.py"
      provides: "YOLOv8 detection logic"
      exports: ["YOLODetector"]
    - path: "config.yaml"
      provides: "Model configuration"
      contains: "model:"
    - path: "models/"
      provides: "Model storage directory"
  key_links:
    - from: "main.py"
      to: "src/detector.py"
      via: "YOLODetector class"
      pattern: "from src.detector import"
---

<objective>
Configure and validate YOLOv8 pre-trained model for people detection. Since COCO pre-trained model includes "person" class, no custom training needed - just validate inference works.

Purpose: Ensure the detection model is ready for real-time inference in Phase 04.
Output: Working YOLOv8 detection, validated on sample inputs.
</objective>

<execution_context>
@C:/Users/user/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/phases/03-model-training/03-CONTEXT.md
@.planning/phases/03-model-training/03-RESEARCH.md
</context>

<tasks>

<task type="auto">
  <name>Validate YOLOv8 model loading and inference</name>
  <files>src/detector.py, config.yaml</files>
  <action>
    Test that YOLODetector can load yolov8n.pt model:
    - Ensure detector.py correctly loads ultralytics YOLO
    - Verify person class filtering works (class_id=0)
    - Test detection returns proper format
    Update config.yaml if needed with optimal settings:
    - model: yolov8n.pt (nano for speed)
    - confidence_threshold: 0.3 (balanced)
  </action>
  <verify>python -c "from src.detector import YOLODetector; d=YOLODetector(); d.load_model(); print('Model loaded:', d.is_loaded)"</verify>
  <done>YOLOv8 model loads successfully</done>
</task>

<task type="auto">
  <name>Test detection on sample input</name>
  <files>tests/test_model.py</files>
  <action>
    Create tests/test_model.py:
      - test_model_loads() - verify model can load
      - test_detection_returns_format() - verify detection output format
      - test_person_filter_works() - verify only person class returned
      - test_confidence_threshold() - verify filtering works
    Run tests to validate detection works
  </action>
  <verify>python -m pytest tests/test_model.py -v 2>/dev/null || python tests/test_model.py</verify>
  <done>Detection tests pass</done>
</task>

<task type="auto">
  <name>Create model utilities and configuration</name>
  <files>models/.gitkeep, src/model_utils.py, config.yaml</files>
  <action>
    Create models/ directory for storing custom models (if needed later)
    Create src/model_utils.py:
      - get_model_info() - display model details
      - check_device() - detect CPU/GPU availability
      - benchmark_model() - measure inference speed
    Ensure config.yaml has correct model settings
  </action>
  <verify>python -c "from src.model_utils import check_device; print(check_device())"</verify>
  <done>Model utilities created</done>
</task>

</tasks>

<verification>
- [ ] YOLOv8 model loads (yolov8n.pt)
- [ ] Person detection returns correct format
- [ ] Confidence threshold filtering works
- [ ] Tests pass
- [ ] Model utilities work
</verification>

<success_criteria>
- YOLOv8 model loads and runs inference
- Person class (class 0) correctly filtered
- Detection returns bbox, confidence, class_id
- Model works in real-time (target >10 FPS)
</success_criteria>

<output>
After completion, create `.planning/phases/03-model-training/03-SUMMARY.md`
</output>