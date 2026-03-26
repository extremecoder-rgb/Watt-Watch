---
phase: 01-foundation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [requirements.txt, setup.py, src/__init__.py, src/detector.py, src/utils.py, config.yaml, .gitignore]
autonomous: true
requirements: [FOUNDATION-01]
must_haves:
  truths:
    - "Project dependencies can be installed via pip"
    - "YOLODetector can load YOLOv8 model"
    - "Detector can identify people in frames"
    - "FPS counter logs frame rate"
    - "CLI provides usable interface for detection"
  artifacts:
    - path: "requirements.txt"
      provides: "Python dependencies"
      min_lines: 5
    - path: "src/detector.py"
      provides: "YOLOv8 detection logic"
      exports: ["YOLODetector"]
    - path: "src/utils.py"
      provides: "FPS counter, video utilities"
      exports: ["FPSCounter", "VideoFrameExtractor"]
    - path: "config.yaml"
      provides: "Configuration settings"
  key_links:
    - from: "main.py"
      to: "src/detector.py"
      via: "import YOLODetector"
      pattern: "from src.detector import"
    - from: "main.py"
      to: "src/utils.py"
      via: "import utilities"
      pattern: "from src.utils import"
---

<objective>
Set up the project structure, install dependencies, and create the basic YOLOv8 detection pipeline.

Purpose: Establish foundation for all subsequent phases - without this, no development can proceed.
Output: Working Python project with YOLOv8 detection capability.
</objective>

<execution_context>
@C:/Users/user/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation/01-CONTEXT.md
@.planning/phases/01-foundation/01-RESEARCH.md
</context>

<tasks>

<task type="auto">
  <name>Create project structure and dependencies</name>
  <files>requirements.txt, setup.py, .gitignore</files>
  <action>
    Create requirements.txt with: ultralytics>=8.0.0, opencv-python>=4.8.0, numpy>=1.24.0, torch>=2.0.0, torchvision>=0.15.0, pillow>=10.0.0, pyyaml>=6.0
    Create setup.py for package installation
    Create .gitignore for Python (include __pycache__, .env, venv/, .venv/, *.pyc, models/, data/)
  </action>
  <verify>npm --version fails (not js project), but pip install -r requirements.txt succeeds</verify>
  <done>requirements.txt exists with all dependencies, setup.py is valid, .gitignore created</done>
</task>

<task type="auto">
  <name>Create detection module</name>
  <files>src/__init__.py, src/detector.py, src/utils.py, config.yaml</files>
  <action>
    Create src/__init__.py with package metadata
    Create src/detector.py:
      - class YOLODetector with load_model(), detect_people(frame) methods
      - Uses ultralytics.YOLO with yolov8n.pt (nano for speed)
      - Filters for COCO person class (class_id=0)
      - Returns list of detections with bbox, confidence
    Create src/utils.py:
      - FPSCounter class for tracking frame rate
      - VideoFrameExtractor for reading video files
      - JSONLogger for logging detections and FPS
    Create config.yaml:
      - model: yolov8n.pt
      - confidence_threshold: 0.3
      - person_class_id: 0
      - input_video_path: data/test_clip.mp4
      - output_path: output/
  </action>
  <verify>python -c "from src.detector import YOLODetector; print('Detector loaded')" works</verify>
  <done>All source files created, detector can be imported and instantiated without errors</done>
</task>

<task type="auto">
  <name>Create main entry point and test script</name>
  <files>main.py, test_detection.py</files>
  <action>
    Create main.py:
      - cli entry point using argparse
      - modes: detect (process video/image), live (webcam), benchmark (test on clips)
      - log FPS to logs/fps.log
      - output JSON results to output/detections.json
    Create test_detection.py:
      - test YOLODetector instantiation
      - test on sample image/video if available
      - verify person detection works
  </action>
  <verify>python main.py --help shows usage</verify>
  <done>main.py provides usable CLI, test script runs basic validation</done>
</task>

</tasks>

<verification>
- [ ] Project structure created with proper directories (src, data, models, logs, output, configs)
- [ ] Dependencies can be installed via pip
- [ ] YOLODetector can load model and detect people
- [ ] FPS logging works
- [ ] CLI provides usable interface
- [ ] Test script validates basic functionality
</verification>

<success_criteria>
- YOLOv8 can detect people in frames
- FPS counter reports frames per second
- Project is installable and runnable
- All code is importable without errors
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-SUMMARY.md`
</output>