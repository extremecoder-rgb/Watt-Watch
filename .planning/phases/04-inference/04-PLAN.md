---
phase: 04-inference
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [main.py, config.yaml]
autonomous: true
requirements: [INFERENCE-01]
must_haves:
  truths:
    - "Video processing loop runs continuously"
    - "FPS is tracked and logged in real-time"
    - "Detection results are saved to JSON"
    - "Live mode shows FPS overlay"
  artifacts:
    - path: "main.py"
      provides: "CLI with detect/live/benchmark commands"
      contains: "FPS"
    - path: "logs/fps.log"
      provides: "FPS logging"
    - path: "output/detections.json"
      provides: "Detection results"
  key_links:
    - from: "main.py"
      to: "src/detector.py"
      via: "YOLODetector"
      pattern: "from src.detector"
    - from: "main.py"
      to: "src/utils.py"
      via: "FPSCounter, JSONLogger"
      pattern: "from src.utils"
---

<objective>
Build real-time processing pipeline with continuous video processing, FPS tracking, and result logging.

Purpose: Connect detection model to video input, enable real-time monitoring and logging. This is the core inference engine.
Output: Working pipeline that processes video streams with FPS logging.
</objective>

<execution_context>
@C:/Users/user/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/phases/04-inference/04-CONTEXT.md
@.planning/phases/04-inference/04-RESEARCH.md
</context>

<tasks>

<task type="auto">
  <name>Enhance main.py with real-time processing loop</name>
  <files>main.py</files>
  <action>
    Enhance main.py cmd_detect function:
    - Add continuous processing loop with proper exit handling
    - Integrate FPSCounter for real-time tracking
    - Add FPS logging to logs/fps.log (append mode)
    - Add graceful shutdown (Ctrl+C) with summary
    - Ensure JSON logger saves results on exit
  </action>
  <verify>python main.py detect --help shows updated options</verify>
  <done>main.py enhanced with real-time processing loop</done>
</task>

<task type="auto">
  <name>Enhance live mode with FPS overlay</name>
  <files>main.py</files>
  <action>
    Enhance main.py cmd_live function:
    - Add FPS counter overlay on video display
    - Show current people count overlay
    - Display running average FPS
    - Ensure clean window close on 'q' key
  </action>
  <verify>python main.py live --help shows options</verify>
  <done>Live mode shows FPS and count overlay</done>
</task>

<task type="auto">
  <name>Update config for inference settings</name>
  <files>config.yaml</files>
  <action>
    Update config.yaml with inference-specific settings:
    - Add inference section with buffer_size, timeout
    - Ensure logging section has correct paths
    - Verify test_clips paths point to data/clips/
  </action>
  <verify>cat config.yaml shows all sections</verify>
  <done>Config updated with inference settings</done>
</task>

</tasks>

<verification>
- [ ] main.py detect command processes video continuously
- [ ] FPS logged to logs/fps.log
- [ ] Detection results saved to output/detections.json
- [ ] Live mode shows FPS overlay
- [ ] Config has correct paths
</verification>

<success_criteria>
- Video processing runs continuously until end of video
- FPS tracking works in real-time (>0 FPS displayed)
- Logs created in correct locations
- Clean shutdown on keyboard interrupt
</success_criteria>

<output>
After completion, create `.planning/phases/04-inference/04-SUMMARY.md`
</output>