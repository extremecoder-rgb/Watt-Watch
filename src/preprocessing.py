"""
Low-light preprocessing for improved detection in dark environments.
"""

import numpy as np
from typing import Tuple, List


# Brightness threshold for low-light detection
LOW_LIGHT_THRESHOLD = 50


def detect_low_light(frame: np.ndarray) -> Tuple[bool, float]:
    """
    Detect if frame is low-light.
    
    Args:
        frame: Video frame (BGR format from OpenCV)
        
    Returns:
        Tuple of (is_low_light, brightness_score)
    """
    # Convert to grayscale for brightness calculation
    gray = np.mean(frame, axis=2)
    
    # Calculate mean brightness (0-255)
    brightness = np.mean(gray)
    
    is_low_light = brightness < LOW_LIGHT_THRESHOLD
    
    return is_low_light, float(brightness)


def enhance_frame(frame: np.ndarray) -> np.ndarray:
    """
    Enhance frame for better detection in low-light.
    
    Uses CLAHE (Contrast Limited Adaptive Histogram Equalization)
    to improve visibility in dark regions.
    
    Args:
        frame: Video frame (BGR format)
        
    Returns:
        Enhanced frame (BGR format)
    """
    try:
        import cv2
        
        # Convert to YUV color space
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        
        # Apply CLAHE to Y channel (luminance)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        yuv[:, :, 0] = clahe.apply(yuv[:, :, 0])
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        
        return enhanced
        
    except ImportError:
        # Fallback: simple histogram equalization
        return enhance_frame_fallback(frame)


def enhance_frame_fallback(frame: np.ndarray) -> np.ndarray:
    """Fallback enhancement without cv2."""
    # Simple normalization
    normalized = frame.astype(np.float32)
    normalized = normalized * (255.0 / np.max(normalized))
    return normalized.astype(np.uint8)


class LowLightDetector:
    """Track low-light conditions over time."""
    
    def __init__(self, threshold: float = LOW_LIGHT_THRESHOLD):
        self.threshold = threshold
        self.low_light_count = 0
        self.total_frames = 0
    
    def process(self, frame: np.ndarray) -> Tuple[bool, float, bool]:
        """
        Process a frame for low-light detection.
        
        Args:
            frame: Video frame
            
        Returns:
            Tuple of (is_low_light, brightness, should_enhance)
        """
        self.total_frames += 1
        
        is_low_light, brightness = detect_low_light(frame)
        
        if is_low_light:
            self.low_light_count += 1
        
        # Enhance if low-light
        should_enhance = is_low_light
        
        return is_low_light, brightness, should_enhance
    
    def get_stats(self) -> dict:
        """Get low-light statistics."""
        if self.total_frames == 0:
            return {
                'total_frames': 0,
                'low_light_frames': 0,
                'percentage': 0.0
            }
        
        return {
            'total_frames': self.total_frames,
            'low_light_frames': self.low_light_count,
            'percentage': (self.low_light_count / self.total_frames) * 100
        }


def create_low_light_detector(threshold: float = LOW_LIGHT_THRESHOLD) -> LowLightDetector:
    """Factory function to create LowLightDetector."""
    return LowLightDetector(threshold=threshold)