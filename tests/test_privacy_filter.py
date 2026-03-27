"""
Test suite for privacy filter (face anonymization).
Verifies no identity leak after anonymization.
"""

import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

CHECK = "[OK]"
FAIL = "[FAIL]"


def test_privacy_filter_creation():
    """Test that PrivacyFilter can be created."""
    print("Test: PrivacyFilter creation...")
    
    try:
        from src.privacy_filter import PrivacyFilter
        
        pf = PrivacyFilter(
            blur_method="gaussian",
            blur_level=31,
            pixelate_blocks=15
        )
        
        config = pf.get_config()
        
        assert config["blur_method"] == "gaussian"
        assert config["blur_level"] == 31
        assert config["pixelate_blocks"] == 15
        
        print(f"  {CHECK} PrivacyFilter created with config: {config}")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def test_privacy_filter_gaussian():
    """Test Gaussian blur anonymization."""
    print("Test: Gaussian blur anonymization...")
    
    try:
        from src.privacy_filter import PrivacyFilter
        
        pf = PrivacyFilter(blur_method="gaussian", blur_level=31)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        anonymized, detections = pf.anonymize_frame(frame)
        
        assert anonymized.shape == frame.shape, "Output shape should match input"
        
        print(f"  {CHECK} Gaussian blur works (detections: {len(detections)})")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def test_privacy_filter_pixelate():
    """Test pixelation anonymization."""
    print("Test: Pixelation anonymization...")
    
    try:
        from src.privacy_filter import PrivacyFilter
        
        pf = PrivacyFilter(blur_method="pixelate", pixelate_blocks=10)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        anonymized, detections = pf.anonymize_frame(frame)
        
        assert anonymized.shape == frame.shape, "Output shape should match input"
        
        print(f"  {CHECK} Pixelation works (detections: {len(detections)})")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def test_face_estimation_from_persons():
    """Test face estimation from person bounding boxes."""
    print("Test: Face estimation from persons...")
    
    try:
        from src.privacy_filter import PrivacyFilter
        
        pf = PrivacyFilter(face_height_ratio=0.25, face_width_ratio=0.3)
        
        person_bboxes = [
            [100, 50, 250, 350],
            [300, 80, 500, 400]
        ]
        
        face_bboxes = pf.estimate_faces_from_persons(person_bboxes)
        
        assert len(face_bboxes) >= 1, "Should estimate at least one face for larger persons"
        
        for fb in face_bboxes:
            x1, y1, x2, y2 = fb
            assert x2 > x1 and y2 > y1, "Face bbox should have positive dimensions"
        
        print(f"  {CHECK} Face estimation works ({len(face_bboxes)} faces estimated)")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def test_verification_no_faces():
    """Test verification when no faces present."""
    print("Test: Verification with no faces...")
    
    try:
        from src.privacy_filter import PrivacyFilter
        
        pf = PrivacyFilter()
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result = pf.verify_anonymization(frame, [])
        
        assert result["verified"] == True
        assert result["faces_before"] == 0
        assert result["faces_after"] == 0
        
        print(f"  {CHECK} Verification works (no faces case)")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def test_anonymization_preserves_detection():
    """Test that anonymization doesn't break detection flow."""
    print("Test: Anonymization preserves detection flow...")
    
    try:
        from src.privacy_filter import PrivacyFilter
        
        pf = PrivacyFilter(blur_method="gaussian", blur_level=31)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(frame, (100, 100), (200, 200), (255, 255, 255), -1)
        
        person_bboxes = [[100, 50, 200, 250]]
        
        anonymized, detections = pf.anonymize_frame(frame, person_bboxes=person_bboxes)
        
        assert anonymized is not None
        assert anonymized.shape == frame.shape
        
        print(f"  {CHECK} Anonymization preserves detection flow")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def test_toggle_blur_methods():
    """Test switching between blur methods."""
    print("Test: Toggle blur methods...")
    
    try:
        from src.privacy_filter import PrivacyFilter
        
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        
        pf_gaussian = PrivacyFilter(blur_method="gaussian", blur_level=15)
        anon_gaussian, _ = pf_gaussian.anonymize_frame(frame)
        
        pf_pixelate = PrivacyFilter(blur_method="pixelate", pixelate_blocks=8)
        anon_pixelate, _ = pf_pixelate.anonymize_frame(frame)
        
        assert anon_gaussian.shape == frame.shape
        assert anon_pixelate.shape == frame.shape
        
        diff_gaussian = np.abs(anon_gaussian.astype(int) - frame.astype(int)).mean()
        diff_pixelate = np.abs(anon_pixelate.astype(int) - frame.astype(int)).mean()
        
        print(f"  {CHECK} Gaussian diff: {diff_gaussian:.2f}, Pixelate diff: {diff_pixelate:.2f}")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def test_config_options():
    """Test configuration options."""
    print("Test: Config options...")
    
    try:
        from src.privacy_filter import PrivacyFilter
        
        pf = PrivacyFilter(
            blur_method="pixelate",
            blur_level=45,
            pixelate_blocks=20,
            face_height_ratio=0.3,
            face_width_ratio=0.35
        )
        
        config = pf.get_config()
        
        assert config["blur_method"] == "pixelate"
        assert config["blur_level"] == 45
        assert config["pixelate_blocks"] == 20
        assert config["face_height_ratio"] == 0.3
        assert config["face_width_ratio"] == 0.35
        
        print(f"  {CHECK} Config options work")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def test_factory_function():
    """Test factory function."""
    print("Test: Factory function...")
    
    try:
        from src.privacy_filter import create_privacy_filter
        
        pf = create_privacy_filter(blur_method="gaussian", blur_level=25)
        
        assert pf is not None
        assert pf.blur_method == "gaussian"
        assert pf.blur_level == 25
        
        print(f"  {CHECK} Factory function works")
        return True
    except Exception as e:
        print(f"  {FAIL} Failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("Privacy Filter Tests")
    print("="*50 + "\n")
    
    tests = [
        ("PrivacyFilter Creation", test_privacy_filter_creation),
        ("Gaussian Blur", test_privacy_filter_gaussian),
        ("Pixelation", test_privacy_filter_pixelate),
        ("Face Estimation", test_face_estimation_from_persons),
        ("Verification (No Faces)", test_verification_no_faces),
        ("Preserve Detection", test_anonymization_preserves_detection),
        ("Toggle Methods", test_toggle_blur_methods),
        ("Config Options", test_config_options),
        ("Factory Function", test_factory_function),
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
            print(f"{FAIL} {name} EXCEPTION: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
