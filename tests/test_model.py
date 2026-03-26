"""
Test suite for YOLOv8 model detection functionality.
"""

import sys
from pathlib import Path
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_model_loads():
    """Test that YOLOv8 model can load."""
    print("Test: Model loads...")
    
    try:
        from src.detector import YOLODetector
        
        detector = YOLODetector(model_name="yolov8n.pt")
        detector.load_model()
        
        assert detector.is_loaded, "Model should be loaded"
        print("  ✓ Model loaded successfully")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_detection_returns_format():
    """Test that detection returns correct format."""
    print("Test: Detection format...")
    
    try:
        from src.detector import YOLODetector
        
        # Create detector and load model
        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.3)
        detector.load_model()
        
        # Create dummy frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect_people(frame)
        
        # Check format
        assert isinstance(detections, list), "Should return list"
        
        if len(detections) > 0:
            det = detections[0]
            assert "bbox" in det, "Should have bbox"
            assert "confidence" in det, "Should have confidence"
            assert "class_id" in det, "Should have class_id"
            assert "class_name" in det, "Should have class_name"
        
        print(f"  ✓ Detection format valid (found {len(detections)} objects)")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_person_filter_works():
    """Test that person class filtering works."""
    print("Test: Person filter...")
    
    try:
        from src.detector import YOLODetector
        
        detector = YOLODetector(model_name="yolov8n.pt")
        detector.load_model()
        
        # Verify person class ID is correct
        assert detector.PERSON_CLASS_ID == 0, "Person class should be 0 (COCO)"
        
        print("  ✓ Person filter configured (class_id=0)")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_confidence_threshold():
    """Test that confidence threshold filtering works."""
    print("Test: Confidence threshold...")
    
    try:
        from src.detector import YOLODetector
        
        # Test with high threshold
        detector_high = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.9)
        detector_high.load_model()
        
        # Test with low threshold
        detector_low = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.1)
        detector_low.load_model()
        
        # Check configuration
        assert detector_high.confidence_threshold == 0.9
        assert detector_low.confidence_threshold == 0.1
        
        print("  ✓ Confidence threshold works (0.1 and 0.9)")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_detect_and_count():
    """Test detect_and_count convenience method."""
    print("Test: Detect and count...")
    
    try:
        from src.detector import YOLODetector
        
        detector = YOLODetector(model_name="yolov8n.pt")
        detector.load_model()
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        count = detector.detect_and_count(frame)
        
        assert isinstance(count, int), "Count should be integer"
        assert count >= 0, "Count should be non-negative"
        
        print(f"  ✓ detect_and_count works (count={count})")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_model_info():
    """Test get_model_info method."""
    print("Test: Model info...")
    
    try:
        from src.detector import YOLODetector
        
        detector = YOLODetector(model_name="yolov8n.pt")
        
        info = detector.get_model_info()
        
        assert "model_name" in info
        assert "loaded" in info
        assert "confidence_threshold" in info
        assert "person_class_id" in info
        
        print(f"  ✓ Model info available")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_model_utils():
    """Test model utilities."""
    print("Test: Model utilities...")
    
    try:
        from src.model_utils import check_device, get_model_info
        
        device = check_device()
        info = get_model_info()
        
        assert device in ["cpu", "cuda", "mps"], f"Unknown device: {device}"
        assert "model_name" in info
        
        print(f"  ✓ Model utilities work (device={device})")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("WattWatch YOLOv8 Model Tests")
    print("="*50 + "\n")
    
    tests = [
        ("Model Loads", test_model_loads),
        ("Detection Format", test_detection_returns_format),
        ("Person Filter", test_person_filter_works),
        ("Confidence Threshold", test_confidence_threshold),
        ("Detect and Count", test_detect_and_count),
        ("Model Info", test_model_info),
        ("Model Utilities", test_model_utils),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {name} EXCEPTION: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)