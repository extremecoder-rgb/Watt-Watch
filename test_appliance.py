#!/usr/bin/env python3
"""
Test script for appliance status recognition.
Tests Light ON/OFF and Ceiling Fan ON/OFF detection using Roboflow API.
"""

import sys
import cv2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.appliance_status import ApplianceStatusRecognizer, Status


def test_appliance_recognition():
    """Test appliance status recognition on sample images."""
    print("Testing Appliance Status Recognition...")
    print("=" * 50)
    
    recognizer = ApplianceStatusRecognizer()
    
    # Test data directory
    test_dir = Path("data")
    
    # Check if test images exist
    test_images = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    
    if not test_images:
        print("No test images found in data directory.")
        print("Using webcam or creating test frame...")
        
        # Create a simple test frame
        test_frame = cv2.imread("data/clips/empty.mp4")
        
        if test_frame is not None:
            print("\nTesting with video frame...")
            results = recognizer.detect_all_appliances(test_frame)
            
            for result in results:
                print(f"\n{result.appliance_type.value}:")
                print(f"  Status: {result.status.value}")
                print(f"  Confidence: {result.confidence:.2f}")
        else:
            print("Could not load test frame from video.")
            return 1
    
    return 0


def demo_single_detection():
    """Demo detecting appliance status on a single image."""
    print("\n" + "=" * 50)
    print("Single Image Detection Demo")
    print("=" * 50)
    
    recognizer = ApplianceStatusRecognizer()
    
    # Try to use first available image
    import glob
    images = glob.glob("data/*.jpg") + glob.glob("data/*.png") + glob.glob("data/**/*.jpg")
    
    if images:
        image_path = images[0]
        print(f"Using image: {image_path}")
        
        frame = cv2.imread(image_path)
        if frame is not None:
            results = recognizer.detect_all_appliances(frame)
            
            for result in results:
                print(f"\n{result.appliance_type.value}:")
                print(f"  Status: {result.status.value}")
                print(f"  Confidence: {result.confidence:.2f}")
    else:
        print("No images found for testing.")
    
    return 0


if __name__ == "__main__":
    test_appliance_recognition()
    demo_single_detection()