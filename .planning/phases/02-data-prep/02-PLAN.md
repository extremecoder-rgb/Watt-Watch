---
phase: 02-data-prep
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [data/clips/.gitkeep, data/raw/.gitkeep, data/processed/.gitkeep, data/annotations/.gitkeep, scripts/video_validator.py, scripts/download_samples.py, scripts/extract_frames.py]
autonomous: true
requirements: [DATA-01]
must_haves:
  truths:
    - "Data directory structure created"
    - "Test video clips accessible (placeholder or samples)"
    - "Video validation script works"
    - "Frame extraction script works"
    - "Test clip metadata documented"
  artifacts:
    - path: "data/clips/"
      provides: "Test video storage"
    - path: "scripts/video_validator.py"
      provides: "Video validation"
      exports: ["validate_video", "get_video_info"]
    - path: "scripts/extract_frames.py"
      provides: "Frame extraction"
      exports: ["extract_frames", "extract_at_interval"]
  key_links:
    - from: "main.py"
      to: "data/clips/"
      via: "config.yaml test_clips path"
      pattern: "test_clips:"
    - from: "scripts/"
      to: "src/utils.py"
      via: "import utilities"
      pattern: "from src.utils import"
---

<objective>
Prepare training/validation data and video test clips for evaluation. Create data directory structure, prepare placeholder videos or download sample videos, and implement validation/extraction scripts.

Purpose: Without test data, we cannot evaluate the detection system. This phase ensures all necessary data is in place for Phase 06 testing.
Output: Data directories, validation scripts, and placeholder/test videos ready for evaluation.
</objective>

<execution_context>
@C:/Users/user/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/phases/02-data-prep/02-CONTEXT.md
@.planning/phases/02-data-prep/02-RESEARCH.md
</context>

<tasks>

<task type="auto">
  <name>Create data directory structure</name>
  <files>data/clips/.gitkeep, data/raw/.gitkeep, data/processed/.gitkeep, data/annotations/.gitkeep</files>
  <action>
    Create directory structure:
    - data/clips/ - test video storage
    - data/raw/ - raw video for processing
    - data/processed/ - preprocessed frames
    - data/annotations/ - ground truth labels
    Use .gitkeep files to preserve empty directories in git
  </action>
  <verify>ls -la data/ shows all subdirectories</verify>
  <done>Data directory structure created with all required subdirectories</done>
</task>

<task type="auto">
  <name>Create sample test videos and validation script</name>
  <files>scripts/video_validator.py, scripts/download_samples.py</files>
  <action>
    Create scripts/video_validator.py:
      - validate_video(path) - checks video file integrity
      - get_video_info(path) - returns fps, resolution, frame_count, duration
      - validate_directory(path) - checks all videos in directory
    Create scripts/download_samples.py:
      - download_yolo_samples() - downloads sample videos from Ultralytics
      - download_url(url, output) - generic downloader
  </action>
  <verify>python -c "from scripts.video_validator import validate_video; print('OK')" works</verify>
  <done>Video validation and sample download scripts created</done>
</task>

<task type="auto">
  <name>Create frame extraction script</name>
  <files>scripts/extract_frames.py</files>
  <action>
    Create scripts/extract_frames.py:
      - extract_frames(video_path, output_dir, count) - extract N frames evenly
      - extract_at_interval(video_path, output_dir, interval) - extract every N frames
      - batch_extract(video_dir, output_dir) - process multiple videos
      - Creates output directory if needed
  </action>
  <verify>python -c "from scripts.extract_frames import extract_frames; print('OK')" works</verify>
  <done>Frame extraction script created and importable</done>
</task>

<task type="auto">
  <name>Document test clip requirements and create placeholders</name>
  <files>docs/TEST_CLIPS.md, data/clips/README.md</files>
  <action>
    Create docs/TEST_CLIPS.md with:
      - Description of each test clip (occupied, empty, quiet-reader)
      - Technical requirements (resolution, fps, duration)
      - How to obtain/procure each clip type
      - Expected behavior for each clip
    Create data/clips/README.md with quick reference
    Create placeholder files or attempt to download sample videos
  </action>
  <verify>cat docs/TEST_CLIPS.md shows all requirements</verify>
  <done>Test clip requirements documented</done>
</task>

</tasks>

<verification>
- [ ] Data directory structure created (clips, raw, processed, annotations)
- [ ] Video validator script works on valid videos
- [ ] Frame extraction script works
- [ ] Test clip requirements documented
- [ ] Config.yaml references updated to point to data/clips
</verification>

<success_criteria>
- Data directories exist and are accessible
- Video validation works
- Frame extraction works
- Test clip requirements documented for Phase 06
</success_criteria>

<output>
After completion, create `.planning/phases/02-data-prep/02-SUMMARY.md`
</output>