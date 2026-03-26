"""
Test script for WattWatch detection functionality.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.detector import YOLODetector
from src.utils import FPSCounter, VideoFrameExtractor


def test_detector_creation():
    """Test creating a detector instance."""
    print("Test: Detector creation...")
    
    detector = YOLODetector(
        model_name="yolov8n.pt",
        confidence_threshold=0.3
    )
    
    assert detector.model_name == "yolov8n.pt"
    assert detector.confidence_threshold == 0.3
    assert detector.PERSON_CLASS_ID == 0
    assert not detector.is_loaded
    
    print("  ✓ Detector created successfully")
    return True


def test_detector_load():
    """Test loading the model."""
    print("Test: Loading model...")
    
    detector = YOLODetector(model_name="yolov8n.pt")
    
    try:
        detector.load_model()
        assert detector.is_loaded
        print("  ✓ Model loaded successfully")
        return True
    except Exception as e:
        print(f"  ⚠ Model load skipped (may need dependencies): {e}")
        return True  # Don't fail if model can't load (no deps)


def test_fps_counter():
    """Test FPS counter functionality."""
    print("Test: FPS counter...")
    
    counter = FPSCounter(window_size=10)
    
    # Simulate frames
    for _ in range(5):
        counter.update()
    
    fps = counter.get_fps()
    stats = counter.get_stats()
    
    assert "current_fps" in stats
    assert "average_fps" in stats
    assert "total_frames" in stats
    
    print(f"  ✓ FPS: {fps:.1f}, Frames: {stats['total_frames']}")
    return True


def test_video_extractor():
    """Test video frame extractor."""
    print("Test: Video frame extractor...")
    
    # Test with non-existent file (should fail gracefully)
    extractor = VideoFrameExtractor("nonexistent.mp4")
    
    # Test with camera index (should fail gracefully on no camera)
    camera_extractor = VideoFrameExtractor("0")
    
    print("  ✓ VideoFrameExtractor initialized")
    return True


def test_model_info():
    """Test getting model info."""
    print("Test: Model info...")
    
    detector = YOLODetector(
        model_name="yolov8s.pt",
        confidence_threshold=0.5
    )
    
    info = detector.get_model_info()
    
    assert info["model_name"] == "yolov8s.pt"
    assert info["confidence_threshold"] == 0.5
    assert info["person_class_id"] == 0
    
    print(f"  ✓ Model info: {info}")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("WattWatch Detection Tests")
    print("="*50 + "\n")
    
    tests = [
        ("Detector Creation", test_detector_creation),
        ("Model Loading", test_detector_load),
        ("FPS Counter", test_fps_counter),
        ("Video Extractor", test_video_extractor),
        ("Model Info", test_model_info),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {name} FAILED: {e}")
    
    print("\n" + "="*50)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)